from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or not email.split("@", 1)[1]:
        raise ValueError("invalid email address")
    return email


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    farm_id: UUID | None
    is_active: bool

    @field_validator("email")
    @classmethod
    def email_lower(cls, value: str) -> str:
        return _normalize_email(value)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def email_lower(cls, value: str) -> str:
        return _normalize_email(value)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
