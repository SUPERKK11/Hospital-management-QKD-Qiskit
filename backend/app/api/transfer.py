from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from datetime import datetime
import logging
import hashlib

# Database & Auth
from app.db.mongodb import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.auth import get_current_user

# Encryption & QKD Tools
# Ensure these utility files exist in your app/utils folder!
from app.utils.encryption import encrypt_data, decrypt_data 
from app.utils.quantum import simulate_qkd_exchange 

router = APIRouter()
logger = logging.getLogger(__name__)

# Input Models
class BatchTransferRequest(BaseModel):
    record_ids: List[str]
    target_hospital_name: str

class AcceptRequest(BaseModel):
    inbox_id: str

# Helper to safely get hospital name
def get_hospital_name(user: dict) -> str:
    # Tries 'hospital_name' first, then 'hospital', then defaults to Unknown
    return user.get("hospital_name", user.get("hospital", "Unknown"))

# ==========================================
# 1. SEND TRANSFER (Doctor A -> Doctor B)
# ==========================================
@router.post("/execute-batch")
async def execute_batch_transfer(
    req: BatchTransferRequest, 
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    summary = { "success": [], "skipped": [], "failed": [] }
    
    # 1. Setup Target Collection
    safe_target_name = req.target_hospital_name.lower().strip().replace(" ", "_")
    target_collection_name = f"inbox_{safe_target_name}"
    
    sender_name = get_hospital_name(current_user)

    for rid in req.record_ids:
        try:
            if not ObjectId.is_valid(rid):
                summary["failed"].append({"id": rid, "reason": "Invalid ID"})
                continue

            # 2. Fetch Source Record
            record = await db["records"].find_one({"_id": ObjectId(rid)})
            if not record:
                summary["failed"].append({"id": rid, "reason": "Not Found"})
                continue

            # 3. Decrypt Source (if it was encrypted) to prepare for QKD
            storage_key = record.get("quantum_key")
            plain_diagnosis = record["diagnosis"]
            if storage_key:
                try:
                    plain_diagnosis = decrypt_data(record["diagnosis"], storage_key)
                except Exception:
                    pass # Fallback to existing value if decryption fails

            # 4. Generate Signature (Prevents Duplicates)
            raw_data_string = f"{record.get('patient_id')}-{plain_diagnosis}"
            data_signature = hashlib.sha256(raw_data_string.encode()).hexdigest()

            # 5. Check if already sent
            existing = await db[target_collection_name].find_one({
                "original_record_id": rid, "data_signature": data_signature
            })
            if existing:
                summary["skipped"].append(rid)
                continue 

            # 6. QKD ENCRYPTION
            qkd_session = simulate_qkd_exchange()
            transmission_key = qkd_session["final_key"]
            secure_diagnosis = encrypt_data(plain_diagnosis, transmission_key)

            # 7. Send to Target Inbox
            transfer_packet = {
                "original_record_id": rid,
                "sender_hospital": sender_name,
                "received_from": sender_name,
                "target_hospital": req.target_hospital_name, 
                "patient_id": record.get("patient_id"),
                "patient_email": record.get("patient_email"),
                "patient_abha": record.get("patient_abha"),
                "encrypted_diagnosis": secure_diagnosis, # Encrypted!
                "prescription": record.get("prescription"),
                "decryption_key": transmission_key,      # Key for receiver
                "data_signature": data_signature,
                "received_at": datetime.now(),
                "status": "LOCKED"
            }
            await db[target_collection_name].insert_one(transfer_packet)

            # 8. Audit Log
            await db["audit_logs"].insert_one({
                "sender_hospital": sender_name,
                "receiver_hospital": req.target_hospital_name,
                "record_id": rid,
                "status": "SECURE TRANSFER",
                "timestamp": datetime.now()
            })
            summary["success"].append(rid)

        except Exception as e:
            logger.error(f"Error processing {rid}: {e}")
            summary["failed"].append({"id": rid, "reason": str(e)})

    return summary

# ==========================================
# 2. VIEW INBOX (Doctor B Views Encrypted Data)
# ==========================================
@router.get("/my-inbox")
async def get_my_hospital_inbox(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    my_hospital = get_hospital_name(current_user)
    if my_hospital == "Unknown": return []

    safe_name = my_hospital.lower().strip().replace(" ", "_")
    collection_name = f"inbox_{safe_name}"

    inbox_records = await db[collection_name].find().sort("received_at", -1).limit(50).to_list(50)

    formatted_records = []
    for rec in inbox_records:
        rec["id"] = str(rec["_id"])
        del rec["_id"]
        rec["sender"] = rec.get("received_from", "Unknown")
        # 🔒 MASK THE DATA IN THE INBOX
        rec["diagnosis"] = "🔒 Encrypted Content" 
        rec["prescription"] = str(rec.get("encrypted_diagnosis", ""))[:40] + "..."
        formatted_records.append(rec)

    return formatted_records

# ==========================================
# 3. ACCEPT TRANSFER (Doctor B Decrypts & Claims)
# ==========================================
@router.post("/accept")
async def accept_transfer(
    req: AcceptRequest, 
    current_user: dict = Depends(get_current_user), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # 1. Identify Inbox
    my_hospital = get_hospital_name(current_user)
    safe_name = my_hospital.lower().strip().replace(" ", "_")
    inbox_collection = f"inbox_{safe_name}"

    if not ObjectId.is_valid(req.inbox_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    # 2. Find Record
    record_in_inbox = await db[inbox_collection].find_one({"_id": ObjectId(req.inbox_id)})
    if not record_in_inbox:
        raise HTTPException(status_code=404, detail="Record not found in Inbox")

    # 3. DECRYPT (Simulate Key Usage)
    try:
        key = record_in_inbox.get("decryption_key")
        encrypted_text = record_in_inbox.get("encrypted_diagnosis")
        
        # Calls your utils/encryption.py
        decrypted_diagnosis = decrypt_data(encrypted_text, key)
    except Exception as e:
        print(f"Decryption failed: {e}")
        decrypted_diagnosis = "Decryption Error - Manual Review Needed"

    # 4. Create NEW record in Main History
    # ⚠️ We assign YOU (current_user) as the doctor so it shows in your dashboard
    new_record = {
        "doctor_id": str(current_user["_id"]),  
        "doctor_name": current_user["full_name"],
        "hospital": my_hospital,
        
        # Copied Data
        "patient_email": record_in_inbox.get("patient_email"),
        "patient_abha": record_in_inbox.get("patient_abha"),
        "patient_id": record_in_inbox.get("patient_id"),
        "diagnosis": decrypted_diagnosis,     
        "prescription": record_in_inbox.get("prescription"), 
        
        "created_at": datetime.now(),
        "transferred_from": record_in_inbox.get("sender_hospital"),
        "is_transferred": True
    }

    await db["records"].insert_one(new_record)

    # 5. Cleanup Inbox
    await db[inbox_collection].delete_one({"_id": ObjectId(req.inbox_id)})

    return {"status": "success", "message": "Patient accepted into your database"}