from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location_region: str = Field(min_length=1, max_length=255)
    capacity: int = Field(ge=0)
    supervisor_id: UUID | None = None


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location_region: str | None = Field(default=None, min_length=1, max_length=255)
    capacity: int | None = Field(default=None, ge=0)
    supervisor_id: UUID | None = None


class FarmPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location_region: str
    capacity: int
    supervisor_id: UUID | None
    created_at: datetime
