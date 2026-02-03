from pydantic import BaseModel, EmailStr, Field, BeforeValidator, ConfigDict
from typing import Optional, Annotated
from bson import ObjectId

# 1. Create a tool to convert ObjectId -> String automatically
# This runs str(value) before Pydantic tries to validate it
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    user_type: str 

class PatientCreate(UserBase):
    abha_id: str
    age: int
    address: str
    password: str

class DoctorCreate(UserBase):
    license_id: str
    hospital_name: str
    password: str

class UserResponse(UserBase):
    # 2. Use the PyObjectId tool here
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    # 3. Modern Pydantic V2 Configuration
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )