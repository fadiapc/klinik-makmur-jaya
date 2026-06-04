from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_id: int
    phone: Optional[str] = None
    is_active: bool = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class UserFilterParams(BaseModel):
    q: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
