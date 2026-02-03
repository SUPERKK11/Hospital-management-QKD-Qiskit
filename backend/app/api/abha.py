from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import get_database
import random

# ✅ CORRECT IMPORT: Getting auth from the same folder
from app.api.auth import get_current_user 

router = APIRouter()

# ---------------------------------------------------------
# 🇮🇳 MOCK ABHA (Ayushman Bharat) SERVICE
# ---------------------------------------------------------

@router.post("/request-otp")
async def request_aadhaar_otp(aadhaar: str):
    # Step 1: Verify format (12 digits)
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Aadhaar Number")
    
    mock_otp = str(random.randint(100000, 999999))
    
    return {
        "message": "OTP sent",
        "mock_otp": mock_otp 
    }

@router.post("/verify-otp")
async def verify_otp_and_create_abha(aadhaar: str, otp: str, current_user: dict = Depends(get_current_user)):
    # Step 2: Verify OTP
    if len(otp) != 6:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Generate ABHA ID
    clean_name = current_user["full_name"].lower().replace(" ", ".")
    abha_address = f"{clean_name}@abdm"
    
    # Save to Database
    db = await get_database()
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"abha_id": abha_address, "aadhaar_linked": True}}
    )

    return {
        "success": True,
        "abha_address": abha_address
    }