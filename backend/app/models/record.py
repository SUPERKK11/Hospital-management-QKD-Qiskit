from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- 1. EXISTING RECORD MODELS ---
class RecordCreate(BaseModel):
    # Doctor can find patient by Email OR ABHA (Either/Or Logic)
    patient_email: Optional[EmailStr] = None
    patient_abha: Optional[str] = None
    
    diagnosis: str
    prescription: str

class RecordResponse(BaseModel):
    id: str = Field(alias="_id")
    doctor_name: str
    hospital: Optional[str] = "Unknown" 
    
    patient_id: str
    patient_abha: Optional[str] = None 
    
    diagnosis: str
    prescription: str
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

# --- 2. NEW AUDIT LOG MODEL (For Government) ---
class AuditLog(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who started it?
    sender_hospital: str
    sender_doctor: str
    
    # Where did it go?
    receiver_hospital: str
    
    # What was transferred? (Metadata only, NO Medical Data)
    record_id: str
    
    # Security Proof
    qkd_key_id: str  # The unique ID of the quantum key used
    status: str = "SECURE"

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}