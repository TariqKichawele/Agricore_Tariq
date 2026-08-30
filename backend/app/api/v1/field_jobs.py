from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.lookup import require_equipment, require_field_hand, require_field_job
from app.core.database import get_db
from app.models import FieldJob, JobStatus, User, UserRole
from app.schemas.field_job import FieldJobCreate, FieldJobPublic, FieldJobUpdate
from app.services.audit import write_audit
from app.services.persist import commit_session

router = APIRouter(prefix="/field-jobs", tags=["field-jobs"])

admin_only = require_roles(UserRole.ADMIN)


def _jsonable(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if hasattr(value, "value"):
            out[key] = value.value
        elif isinstance(value, UUID):
            out[key] = str(value)
        else:
            out[key] = value
    return out


def _apply_job_refs(db: Session, payload: dict[str, Any]) -> None:
    if payload.get("equipment_id") is not None:
        require_equipment(db, payload["equipment_id"])
    if payload.get("operator_id") is not None:
        require_field_hand(db, payload["operator_id"])


def _visible_job_or_404(db: Session, job_id: UUID, user: User) -> FieldJob:
    job = require_field_job(db, job_id)
    if user.role == UserRole.FIELD_HAND and job.operator_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field job not found")
    if user.role not in (UserRole.ADMIN, UserRole.AUDITOR, UserRole.FIELD_HAND):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return job


@router.get("", response_model=list[FieldJobPublic])
def list_field_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    operator_id: UUID | None = None,
    equipment_id: UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[FieldJob]:
    stmt = select(FieldJob).order_by(FieldJob.created_at.desc())
    if user.role == UserRole.FIELD_HAND:
        stmt = stmt.where(FieldJob.operator_id == user.id)
    elif user.role not in (UserRole.ADMIN, UserRole.AUDITOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if status_filter is not None:
        stmt = stmt.where(FieldJob.status == status_filter)
    if operator_id is not None:
        if user.role == UserRole.FIELD_HAND and operator_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        stmt = stmt.where(FieldJob.operator_id == operator_id)
    if equipment_id is not None:
        stmt = stmt.where(FieldJob.equipment_id == equipment_id)
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())


@router.get("/{job_id}", response_model=FieldJobPublic)
def get_field_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldJob:
    return _visible_job_or_404(db, job_id, user)


@router.post("", response_model=FieldJobPublic, status_code=status.HTTP_201_CREATED)
def create_field_job(
    payload: FieldJobCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> FieldJob:
    data = payload.model_dump()
    _apply_job_refs(db, data)
    job = FieldJob(**data)
    db.add(job)
    write_audit(
        db,
        actor=actor,
        action="create",
        entity_type="field_job",
        entity_id=job.id,
        details=_jsonable(
            {
                "title": job.title,
                "equipment_id": job.equipment_id,
                "operator_id": job.operator_id,
            }
        ),
    )
    commit_session(db)
    db.refresh(job)
    return job


@router.patch("/{job_id}", response_model=FieldJobPublic)
def update_field_job(
    job_id: UUID,
    payload: FieldJobUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldJob:
    job = _visible_job_or_404(db, job_id, user)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if user.role == UserRole.FIELD_HAND:
        extra = set(data) - {"status"}
        if extra:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Field hands can only update job status",
            )
        if job.operator_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field job not found")
    elif user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    else:
        _apply_job_refs(db, data)

    for key, value in data.items():
        setattr(job, key, value)
    write_audit(
        db,
        actor=user,
        action="update",
        entity_type="field_job",
        entity_id=job.id,
        details=_jsonable(data),
    )
    commit_session(db)
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Response:
    job = require_field_job(db, job_id)
    write_audit(
        db,
        actor=actor,
        action="delete",
        entity_type="field_job",
        entity_id=job.id,
        details={"title": job.title},
    )
    db.delete(job)
    commit_session(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
