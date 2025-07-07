from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from models import UserRole, UserStatus


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    group_id: Optional[int]
    username: str
    email: Optional[EmailStr]
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    status: Optional[UserStatus]
    role: Optional[UserRole]

    class Config:
        from_attributes = True
