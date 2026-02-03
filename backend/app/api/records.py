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

# --- 1. CREATE RECORD (The Gatekeeper) ---
@router.post("/create", response_model=RecordResponse)
async def create_record(record: RecordCreate, current_user: dict = Depends(get_current_user)):
    
    # A. AUTHORIZATION CHECK
    # Note: We check 'role' now (updated from 'user_type')
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create records")
    
    db = await get_database()
    
    # B. SMART PATIENT LOOKUP (Email OR ABHA)
    patient = None
    
    if record.patient_abha:
        # Clean the input (remove dashes)
        clean_abha = record.patient_abha.replace("-", "").replace(" ", "")
        patient = await db["users"].find_one({"abha_number": clean_abha})
    elif record.patient_email:
        patient = await db["users"].find_one({"email": record.patient_email})
    else:
        raise HTTPException(status_code=400, detail="Must provide either Patient Email or ABHA Number")

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found. Please check the ID.")

    # -------------------------------------------------------
    # ⚛️ QUANTUM ENCRYPTION STEP
    # -------------------------------------------------------
    qkd_result = simulate_qkd_exchange()
    secret_key = qkd_result['final_key']

    # Encrypt Data
    encrypted_diagnosis = encrypt_data(record.diagnosis, secret_key)
    encrypted_prescription = encrypt_data(record.prescription, secret_key)

    record_dict = record.model_dump()
    
    # Overwrite plain text with Encrypted text
    record_dict["diagnosis"] = encrypted_diagnosis
    record_dict["prescription"] = encrypted_prescription
    record_dict["quantum_key"] = secret_key
    # -------------------------------------------------------

    # C. STAMP METADATA (The Silo)
    record_dict["doctor_id"] = current_user["_id"]
    record_dict["doctor_name"] = current_user["full_name"]
    # This stamps the record with the Doctor's specific hospital (e.g., "hospitalA")
    record_dict["hospital"] = current_user.get("hospital", "Unknown") 
    
    record_dict["patient_id"] = str(patient["_id"])
    record_dict["patient_abha"] = patient.get("abha_number", "N/A")
    record_dict["created_at"] = datetime.utcnow()
    
    # D. SAVE TO DB
    new_record = await db["records"].insert_one(record_dict)
    
    # E. DECRYPT FOR RESPONSE (So the doctor sees what they just wrote)
    created_record = await db["records"].find_one({"_id": new_record.inserted_id})
    created_record["diagnosis"] = decrypt_data(created_record["diagnosis"], secret_key)
    created_record["prescription"] = decrypt_data(created_record["prescription"], secret_key)
    
    created_record["_id"] = str(created_record["_id"]) # Fix ObjectId for Pydantic
    
    return created_record


# --- 2. FETCH RECORDS (The Traffic Cop) ---
@router.get("/my-records")
async def get_my_records(
    current_user: dict = Depends(get_current_user),
    search_abha: Optional[str] = Query(None, description="Search by ABHA"),
    hospital_filter: Optional[str] = Query(None, description="Filter by Hospital")
):
    db = await get_database()
    query = {}
    
    user_role = current_user.get("role")
    
    # --- LOGIC PATH A: DOCTOR (Siloed) ---
    if user_role == "doctor":
        # Rule: Can ONLY see records from THEIR hospital
        query["hospital"] = current_user.get("hospital")
        
        # Optional: Search for a specific patient within their hospital
        if search_abha:
            query["patient_abha"] = search_abha.replace("-", "").replace(" ", "")

    # --- LOGIC PATH B: PATIENT (Global View) ---
    elif user_role == "patient":
        # Rule: Can ONLY see their OWN records (using ABHA or ID)
        if "abha" in current_user and current_user["abha"]:
            query["patient_abha"] = current_user["abha"]
        else:
             # Fallback for old patients or missing ABHA
             query["patient_id"] = str(current_user["_id"])
        
        # Optional: Filter by hospital ("Show me only Hospital A")
        if hospital_filter:
            query["hospital"] = hospital_filter

    # --- LOGIC PATH C: GOVERNMENT (Super Admin) ---
    elif user_role == "government":
        # Rule: Must search for a specific citizen. Can see ALL hospitals.
        if not search_abha:
            # Return empty if they haven't searched yet (Privacy)
            return [] 
        
        query["patient_abha"] = search_abha.replace("-", "").replace(" ", "")

    # --- EXECUTE QUERY ---
    records = await db["records"].find(query).sort("created_at", -1).to_list(100)
    
    # -------------------------------------------------------
    # ⚛️ QUANTUM DECRYPTION STEP
    # -------------------------------------------------------
    decrypted_records = []
    for rec in records:
        try:
            if "quantum_key" in rec:
                key = rec["quantum_key"]
                rec["diagnosis"] = decrypt_data(rec["diagnosis"], key)
                rec["prescription"] = decrypt_data(rec["prescription"], key)
            
            # Convert ObjectIds to string
            rec["_id"] = str(rec["_id"])
            if "doctor_id" in rec: rec["doctor_id"] = str(rec["doctor_id"])
                
            decrypted_records.append(rec)
        except Exception as e:
            print(f"Decryption Error: {e}")
            decrypted_records.append(rec)
            
    return decrypted_records