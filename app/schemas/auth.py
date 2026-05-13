from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    phone: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
