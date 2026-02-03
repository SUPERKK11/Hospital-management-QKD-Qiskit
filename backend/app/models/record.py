# backend/app/models/record.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- 1. EXISTING RECORD MODELS ---
class RecordCreate(BaseModel):
    # Doctor can find patient by Email OR ABHA
    patient_email: Optional[EmailStr] = None
    patient_abha: Optional[str] = None
    
    diagnosis: str
    prescription: str
    notes: Optional[str] = None  # <--- ADD THIS LINE ✅

class RecordResponse(BaseModel):
    id: str = Field(alias="_id")
    doctor_name: str
    hospital: Optional[str] = "Unknown" 
    
    patient_id: str
    patient_abha: Optional[str] = None 
    
    diagnosis: str
    prescription: str
    notes: Optional[str] = None # <--- ADD THIS LINE TOO ✅
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

# --- 2. AUDIT LOG MODEL ---
class AuditLog(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_hospital: str
    sender_doctor: str
    receiver_hospital: str
    record_id: str
    qkd_key_id: str
    status: str = "SECURE"

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}