from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EquipmentStatus


class EquipmentCreate(BaseModel):
    serial_number: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    status: EquipmentStatus = EquipmentStatus.IDLE
    fuel_level: int = Field(default=100, ge=0, le=100)
    facility_id: UUID
    assigned_operator_id: UUID | None = None


class EquipmentUpdate(BaseModel):
    serial_number: str | None = Field(default=None, min_length=1, max_length=128)
    model: str | None = Field(default=None, min_length=1, max_length=128)
    status: EquipmentStatus | None = None
    fuel_level: int | None = Field(default=None, ge=0, le=100)
    facility_id: UUID | None = None
    assigned_operator_id: UUID | None = None


class EquipmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serial_number: str
    model: str
    status: EquipmentStatus
    fuel_level: int
    facility_id: UUID
    assigned_operator_id: UUID | None
    created_at: datetime
