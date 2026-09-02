from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceReportPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field_job_id: UUID
    file_url: str
    notes: str | None
    created_at: datetime
    download_expires_in: int = Field(description="Presigned URL lifetime in seconds")
