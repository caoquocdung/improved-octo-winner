from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    avatar: Optional[str] = None


class GroupUpdate(BaseModel):
    description: Optional[str] = None
    avatar: Optional[str] = None


class GroupRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    avatar: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
