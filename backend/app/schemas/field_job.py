from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobPriority, JobStatus


class FieldJobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    priority: JobPriority = JobPriority.MEDIUM
    status: JobStatus = JobStatus.PENDING
    equipment_id: UUID
    operator_id: UUID


class FieldJobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    priority: JobPriority | None = None
    status: JobStatus | None = None
    equipment_id: UUID | None = None
    operator_id: UUID | None = None


class FieldJobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    priority: JobPriority
    status: JobStatus
    equipment_id: UUID
    operator_id: UUID
    created_at: datetime
