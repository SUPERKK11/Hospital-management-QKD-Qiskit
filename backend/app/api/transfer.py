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

def get_hospital_name(user: dict) -> str:
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
    sender_name = get_hospital_name(current_user)
    safe_target_name = req.target_hospital_name.lower().strip().replace(" ", "_")
    target_collection_name = f"inbox_{safe_target_name}"

    for rid in req.record_ids:
        try:
            # A. Fetch Source Record
            record = await db["records"].find_one({"_id": ObjectId(rid)})
            if not record:
                summary["failed"].append({"id": rid, "reason": "Not Found"})
                continue

            # B. 🔓 CRITICAL: DECRYPT BEFORE SENDING
            # We must unlock the data locally so we don't send "Double Encrypted" garbage
            plain_diagnosis = record["diagnosis"]
            
            if "quantum_key" in record:
                try:
                    storage_key = record["quantum_key"]
                    plain_diagnosis = decrypt_data(record["diagnosis"], storage_key)
                except Exception as e:
                    print(f"❌ Source Decryption Failed for {rid}: {e}")
                    summary["failed"].append({"id": rid, "reason": "Source Data Corrupt"})
                    continue

            # C. Check Duplicates
            raw_data_string = f"{record.get('patient_id')}-{plain_diagnosis}"
            data_signature = hashlib.sha256(raw_data_string.encode()).hexdigest()

            existing = await db[target_collection_name].find_one({
                "original_record_id": rid, "data_signature": data_signature
            })
            if existing:
                summary["skipped"].append(rid)
                continue 

            # D. ⚛️ RE-ENCRYPT FOR TRANSFER (QKD)
            qkd_session = simulate_qkd_exchange()
            transmission_key = qkd_session["final_key_hash"] 
            
            secure_diagnosis = encrypt_data(plain_diagnosis, transmission_key)

            # E. Send to Inbox
            transfer_packet = {
                "original_record_id": rid,
                "sender_hospital": sender_name,
                "target_hospital": req.target_hospital_name, 
                "patient_id": record.get("patient_id"),
                "patient_email": record.get("patient_email"),
                "patient_abha": record.get("patient_abha"),
                "encrypted_diagnosis": secure_diagnosis, # ✅ Sending Freshly Encrypted Data
                "prescription": record.get("prescription"),
                "decryption_key": transmission_key,     
                "data_signature": data_signature,
                "received_at": datetime.now(),
                "status": "LOCKED"
            }
            await db[target_collection_name].insert_one(transfer_packet)
            
            # F. Audit Log
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
# 2. FETCH INBOX (For Doctor B)
# ==========================================
@router.get("/my-inbox")
async def get_my_inbox(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    my_hospital = get_hospital_name(current_user)
    safe_name = my_hospital.lower().strip().replace(" ", "_")
    collection_name = f"inbox_{safe_name}"
    
    inbox_items = await db[collection_name].find().sort("received_at", -1).to_list(50)
    
    # Return formatted list
    return [{**item, "_id": str(item["_id"])} for item in inbox_items]

# ==========================================
# 3. ACCEPT TRANSFER (The Decryption Step)
# ==========================================
@router.post("/accept")
async def accept_transfer(
    req: AcceptRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    my_hospital = get_hospital_name(current_user)
    safe_name = my_hospital.lower().strip().replace(" ", "_")
    inbox_collection = f"inbox_{safe_name}"

    # A. Find in Inbox
    inbox_item = await db[inbox_collection].find_one({"_id": ObjectId(req.inbox_id)})
    if not inbox_item:
        raise HTTPException(status_code=404, detail="Message not found")

    # B. 🔓 DECRYPT THE TRANSFER
    try:
        key = inbox_item["decryption_key"]
        cipher_text = inbox_item["encrypted_diagnosis"]
        
        # Unlocks the data using the transmission key
        decrypted_diagnosis = decrypt_data(cipher_text, key)
        print(f"✅ Successfully decrypted transfer {req.inbox_id}")
        
    except Exception as e:
        print(f"❌ Decryption Failed: {e}")
        decrypted_diagnosis = "Error: Decryption Failed"

    # C. Create Permanent Record
    # We encrypt it again with a NEW local key for storage
    local_qkd = simulate_qkd_exchange()
    local_key = local_qkd["final_key_hash"]
    
    storage_diagnosis = encrypt_data(decrypted_diagnosis, local_key)

    new_record = {
        "doctor_id": str(current_user["_id"]),
        "doctor_name": current_user["full_name"],
        "hospital": my_hospital,
        "patient_id": inbox_item.get("patient_id"),
        "patient_email": inbox_item.get("patient_email"),
        "patient_abha": inbox_item.get("patient_abha"),
        "diagnosis": storage_diagnosis, # Stored securely
        "prescription": inbox_item.get("prescription"),
        "quantum_key": local_key,       # Store the key to read it later
        "created_at": datetime.now(),
        "transfer_origin": inbox_item.get("sender_hospital")
    }

    await db["records"].insert_one(new_record)

    # D. Remove from Inbox
    await db[inbox_collection].delete_one({"_id": ObjectId(req.inbox_id)})

    return {"status": "Accepted", "message": "Record decrypted and added to your history."}