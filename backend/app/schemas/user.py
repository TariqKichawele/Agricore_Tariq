from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole
from app.schemas.auth import UserPublic, _normalize_email


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole
    farm_id: UUID | None = None
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def email_lower(cls, value: str) -> str:
        return _normalize_email(value)


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    farm_id: UUID | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def email_lower(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_email(value)


__all__ = ["UserCreate", "UserPublic", "UserUpdate"]
