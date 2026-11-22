from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "citizen"  # "admin", "officer", "citizen"
    phone: Optional[str] = None
    badge_id: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    assigned_area: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    approval_status: str = "approved"  # "approved", "pending_approval", "rejected"
    is_active: bool = True
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None

class UserCreate(UserBase):
    password: str

class OfficerRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20)
    employee_id: str = Field(..., min_length=2, max_length=50)
    department: str = Field(..., min_length=2, max_length=100)
    designation: str = Field(..., min_length=2, max_length=100)
    assigned_area: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)

class OfficerReviewAction(BaseModel):
    reason: Optional[str] = None

class OfficerRegistrationResponse(BaseModel):
    id: str
    message: str
    approval_status: str = "pending_approval"
    email: str
    full_name: str
    employee_id: str
    department: str
    designation: str
    assigned_area: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
