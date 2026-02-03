from fastapi import APIRouter, HTTPException, Depends, Query
from app.db.mongodb import get_database
from app.models.record import RecordCreate, RecordResponse
from app.api.auth import get_current_user
from datetime import datetime
from typing import Optional, List

# ⚛️ IMPORT QUANTUM TOOLS
from app.utils.quantum import simulate_qkd_exchange
from app.utils.encryption import encrypt_data, decrypt_data

router = APIRouter()

# --- 1. CREATE RECORD ---
@router.post("/create", response_model=RecordResponse)
async def create_record(record: RecordCreate, current_user: dict = Depends(get_current_user)):
    
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create records")
    
    db = await get_database()
    
    # Clean ABHA (remove dashes) so it stores cleanly
    if record.patient_abha:
        record.patient_abha = record.patient_abha.replace("-", "").replace(" ", "")

    # FIND PATIENT
    patient = None
    if record.patient_abha:
        patient = await db["users"].find_one({"abha_number": record.patient_abha})
    elif record.patient_email:
        patient = await db["users"].find_one({"email": record.patient_email})

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in system. Register them first.")

    # ⚛️ QUANTUM ENCRYPTION
    qkd_result = simulate_qkd_exchange()
    secret_key = qkd_result['final_key_hash'] 

    # Encrypt
    encrypted_diagnosis = encrypt_data(record.diagnosis, secret_key)
    encrypted_prescription = encrypt_data(record.prescription, secret_key)

    record_dict = record.model_dump()
    record_dict["diagnosis"] = encrypted_diagnosis
    record_dict["prescription"] = encrypted_prescription
    record_dict["quantum_key"] = secret_key
    
    # Metadata
    record_dict["doctor_id"] = str(current_user["_id"])
    record_dict["doctor_name"] = current_user["full_name"]
    record_dict["hospital"] = current_user.get("hospital", "Unknown") 
    record_dict["patient_id"] = str(patient["_id"])
    record_dict["patient_abha"] = patient.get("abha_number", "N/A")
    record_dict["created_at"] = datetime.utcnow()
    
    new_record = await db["records"].insert_one(record_dict)
    
    # Decrypt for Response
    created_record = await db["records"].find_one({"_id": new_record.inserted_id})
    created_record["diagnosis"] = decrypt_data(created_record["diagnosis"], secret_key)
    created_record["prescription"] = decrypt_data(created_record["prescription"], secret_key)
    created_record["_id"] = str(created_record["_id"])
    
    return created_record


# --- 2. FETCH RECORDS (FIXED SEARCH) ---
@router.get("/my-records")
async def get_my_records(
    current_user: dict = Depends(get_current_user),
    search_abha: Optional[str] = Query(None, description="Search by ABHA"),
    # ✅ ADDED THIS PARAMETER:
    search_email: Optional[str] = Query(None, description="Search by Email"), 
    hospital_filter: Optional[str] = Query(None, description="Filter by Hospital")
):
    db = await get_database()
    query = {}
    
    user_role = current_user.get("role")
    
    # A. DOCTOR VIEW
    if user_role == "doctor":
        query["hospital"] = current_user.get("hospital")
        
        # ✅ ABHA SEARCH LOGIC
        if search_abha:
            clean_abha = search_abha.replace("-", "").replace(" ", "")
            query["$or"] = [
                {"patient_abha": search_abha}, 
                {"patient_abha": clean_abha}
            ]

        # ✅ EMAIL SEARCH LOGIC (New)
        if search_email:
            query["patient_email"] = {"$regex": search_email, "$options": "i"}

    # B. PATIENT VIEW
    elif user_role == "patient":
        # Patients can only see their own records
        if "abha" in current_user and current_user["abha"]:
            query["patient_abha"] = current_user["abha"]
        else:
             query["patient_id"] = str(current_user["_id"])
        
        if hospital_filter:
            query["hospital"] = hospital_filter

    # C. GOVERNMENT VIEW
    elif user_role == "government":
        if not search_abha:
            return [] 
        query["patient_abha"] = search_abha.replace("-", "").replace(" ", "")

    # EXECUTE QUERY
    records = await db["records"].find(query).sort("created_at", -1).to_list(100)
    
    # ⚛️ DECRYPT RECORDS
    decrypted_records = []
    for rec in records:
        try:
            if "quantum_key" in rec:
                key = rec["quantum_key"]
                rec["diagnosis"] = decrypt_data(rec["diagnosis"], key)
                rec["prescription"] = decrypt_data(rec["prescription"], key)
            
            rec["_id"] = str(rec["_id"])
            if "doctor_id" in rec: rec["doctor_id"] = str(rec["doctor_id"])
                
            decrypted_records.append(rec)
        except Exception as e:
            print(f"Decryption Error for Record {rec.get('_id')}: {e}")
            rec["_id"] = str(rec["_id"])
            # Return it anyway so the doctor sees "Something is there"
            decrypted_records.append(rec)
            
    return decrypted_records