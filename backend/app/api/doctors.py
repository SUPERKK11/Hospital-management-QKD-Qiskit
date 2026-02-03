from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from pydantic import BaseModel
import logging
from app.api.auth import get_current_user # <--- ADD THIS

# ✅ Import get_database to use as a dependency
from app.db.mongodb import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

# --- Response Schema ---
class DoctorResponse(BaseModel):
    id: str
    name: str
    spec: str = "General"
    hospital: str
    status: str = "Available"

# ✅ ROUTE DEFINITION
@router.get("/", response_model=List[DoctorResponse])
async def get_doctors_by_hospital(
    hospital: str = Query(..., description="Hospital Name"),
    # 👇 This "Depends" handles the async connection automatically for you
    db: AsyncIOMotorDatabase = Depends(get_database) 
):
    try:
        print(f"🔍 Searching for doctors in: {hospital}") 

        # 1. Query MongoDB 'users' collection
        # We filter by role="doctor" AND the hospital name
        doctors_cursor = db.users.find(
            {"role": "doctor", "hospital": hospital},
            {"_id": 0, "full_name": 1, "email": 1, "specialization": 1, "hospital": 1}
        )
        
        doctors_list = await doctors_cursor.to_list(length=100)

        # 2. Format data for the Frontend
        formatted_doctors = []
        for doc in doctors_list:
            formatted_doctors.append(DoctorResponse(
                id=doc.get("email", "no-email"), 
                name=doc.get("full_name", "Unknown Doctor"),
                spec=doc.get("specialization", "General Doctor"),
                hospital=doc.get("hospital", hospital),
                status="Available"
            ))

        return formatted_doctors

    except Exception as e:
        logger.error(f"❌ Error fetching doctors: {str(e)}")
        print(f"❌ CRITICAL ERROR: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
# ======================================================
# NEW ENDPOINT: GET TARGET HOSPITALS (Dynamic Filter)
# ======================================================
@router.get("/target-hospitals")
async def get_target_hospitals(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns a list of all hospitals EXCEPT the current user's hospital.
    Used for populating the 'Transfer To' dropdown.
    """
    # 1. Identify "My" Hospital (e.g., "Hospital A")
    my_hospital = current_user.get("hospital")

    # 2. Find all unique hospital names in the database
    # This scans the 'users' collection to see which hospitals exist
    all_hospitals = await db.users.distinct("hospital")

    # 3. Filter the list: Keep everything that is NOT my_hospital
    valid_targets = [
        h for h in all_hospitals 
        if h and h != my_hospital and h != "Unknown"
    ]

    print(f"🏥 User is at {my_hospital}. Available Targets: {valid_targets}")
    return valid_targets