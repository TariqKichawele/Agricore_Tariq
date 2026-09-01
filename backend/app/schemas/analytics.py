from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import EquipmentStatus
from app.schemas.auth import UserPublic
from app.schemas.farm import FarmPublic


class LowFuelItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serial_number: str
    model: str
    status: EquipmentStatus
    fuel_level: int
    facility_id: UUID
    assigned_operator_id: UUID | None


class LowFuelResponse(BaseModel):
    count: int
    items: list[LowFuelItem]


class CoLocationItem(BaseModel):
    equipment_id: UUID
    serial_number: str
    model: str
    facility_id: UUID
    assigned_operator_id: UUID
    operator_farm_id: UUID | None


class CoLocationResponse(BaseModel):
    count: int
    items: list[CoLocationItem]


class ReliabilityRow(BaseModel):
    model: str
    completed: int
    failed: int


class ReliabilityResponse(BaseModel):
    models: list[ReliabilityRow]


class MaintenanceFlagItem(BaseModel):
    farm: FarmPublic
    unit_count: int
    maintenance_count: int
    maintenance_ratio: float


class MaintenanceFlagsResponse(BaseModel):
    count: int
    farms: list[MaintenanceFlagItem]


class ReportingLinesResponse(BaseModel):
    count: int
    field_hands: list[UserPublic]
