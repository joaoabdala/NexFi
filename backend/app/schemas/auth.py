import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class UserProfile(ORMModel):
    id: uuid.UUID
    email: str
    name: str
    timezone: str
    locale: str
    role: UserRole


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    timezone: str | None = None
    locale: str | None = None
