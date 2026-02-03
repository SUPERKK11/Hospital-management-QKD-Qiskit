from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re

# Import your local tools
from app.db.mongodb import get_database
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    SECRET_KEY, 
    ALGORITHM
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# --- 1. UNIFIED DATA MODEL ---
# We use one flexible model to handle inputs from the single Registration Form
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str           # "doctor", "patient", "government"
    
    # ✅ CRITICAL FIX: Must be Optional to accept 'null' from Frontend
    hospital: Optional[str] = None  
    abha_number: Optional[str] = None

    @field_validator('hospital')
    def validate_hospital(cls, v, info):
        # Access other fields
        values = info.data
        
        # Government doesn't need a specific hospital tag
        if 'role' in values and values['role'] == 'government':
            return "National"
        
        # Patient doesn't need a hospital (Ensure it's None)
        if 'role' in values and values['role'] == 'patient':
            return None

        # Doctor MUST have a valid hospital
        if 'role' in values and values['role'] == 'doctor':
            allowed = ["hospitalA", "hospitalB", "hospitalC"]
            if not v:
                 raise ValueError("Doctors must belong to a hospital.")
            if v not in allowed:
                raise ValueError(f"Invalid hospital. Must be one of {allowed}")
        
        return v

    @field_validator('role')
    def validate_role(cls, v):
        if v not in ["doctor", "patient", "government"]:
            raise ValueError("Role must be 'doctor', 'patient', or 'government'")
        return v

# --- 2. SMART REGISTRATION ENDPOINT ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    db = await get_database()
    
    # A. ABHA VALIDATION (For Patients Only)
    clean_abha = None
    if user.role == "patient":
        if not user.abha_number:
            raise HTTPException(status_code=400, detail="ABHA Number is required for patients")
        
        # Remove dashes/spaces
        clean_abha = user.abha_number.replace("-", "").replace(" ", "")
        
        # Strict 14-digit check
        if not clean_abha.isdigit() or len(clean_abha) != 14:
             raise HTTPException(status_code=400, detail="Invalid ABHA Number. Must be exactly 14 digits.")
             
        # Check if ABHA already exists
        if await db["users"].find_one({"abha_number": clean_abha}):
            raise HTTPException(status_code=400, detail="This ABHA Number is already registered")

    # B. Check if Email already exists (For everyone)
    if await db["users"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # C. Hash Password
    hashed_password = get_password_hash(user.password)
    
    # D. Prepare User Object
    new_user = {
        "full_name": user.full_name,
        "email": user.email,
        "password": hashed_password,
        "role": user.role,      
        "hospital": user.hospital,
        "created_at": datetime.utcnow()
    }
    
    # Add ABHA only if patient
    if user.role == "patient":
        new_user["abha_number"] = clean_abha

    # E. Save to DB
    result = await db["users"].insert_one(new_user)
    
    return {
        "id": str(result.inserted_id),
        "message": f"{user.role.capitalize()} registered successfully"
    }

# --- 3. SMART LOGIN (Email OR ABHA) ---
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = await get_database()
    
    # INPUT CLEANING
    login_input = form_data.username.strip()
    
    # SMART QUERY: Check if input matches Email OR ABHA Number
    # If input is digits (14 chars), treat as ABHA. Otherwise treat as Email.
    clean_input = login_input.replace("-", "").replace(" ", "")
    
    query = {}
    if clean_input.isdigit() and len(clean_input) == 14:
        query = {"abha_number": clean_input}
    else:
        query = {"email": login_input}
        
    user = await db["users"].find_one(query)
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email/ABHA or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TOKEN GENERATION
    access_token_expires = timedelta(minutes=60)
    
    # We embed Critical Info in the token so the Frontend is smart
    token_payload = {
        "sub": user["email"], 
        "role": user["role"],
        "hospital": user.get("hospital"),
        "abha": user.get("abha_number") # Embed ABHA if it exists
    }
    
    access_token = create_access_token(
        data=token_payload, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user["role"],
        "hospital": user.get("hospital"),
        "full_name": user["full_name"]
    }

# --- 4. CURRENT USER UTILITY ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = await get_database()
    user = await db["users"].find_one({"email": email})

    if user is None:
        raise credentials_exception

    # Return the user dict (convert ObjectId to str if needed)
    user["_id"] = str(user["_id"])
    return user