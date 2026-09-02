from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.lookup import get_or_404, require_field_job
from app.core.database import get_db
from app.models import ServiceReport, User, UserRole
from app.schemas.service_report import ServiceReportPublic
from app.services import s3 as s3_svc
from app.services.audit import write_audit
from app.services.persist import commit_session

router = APIRouter(prefix="/field-jobs", tags=["service-reports"])


def _visible_job_or_404(db: Session, job_id: UUID, user: User):
    job = require_field_job(db, job_id)
    if user.role == UserRole.FIELD_HAND and job.operator_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field job not found")
    if user.role not in (UserRole.ADMIN, UserRole.AUDITOR, UserRole.FIELD_HAND):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return job


def _can_upload(user: User, job) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.FIELD_HAND and job.operator_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def _public(report: ServiceReport) -> ServiceReportPublic:
    return ServiceReportPublic(
        id=report.id,
        field_job_id=report.field_job_id,
        file_url=s3_svc.presigned_get_url(report.file_url),
        notes=report.notes,
        created_at=report.created_at,
        download_expires_in=s3_svc.PRESIGN_EXPIRES_SECONDS,
    )


@router.get("/{job_id}/reports", response_model=list[ServiceReportPublic])
def list_reports(
    job_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ServiceReportPublic]:
    _visible_job_or_404(db, job_id, user)
    stmt = (
        select(ServiceReport)
        .where(ServiceReport.field_job_id == job_id)
        .order_by(ServiceReport.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return [_public(row) for row in db.scalars(stmt).all()]


@router.get("/{job_id}/reports/{report_id}", response_model=ServiceReportPublic)
def get_report(
    job_id: UUID,
    report_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ServiceReportPublic:
    _visible_job_or_404(db, job_id, user)
    report = get_or_404(db, ServiceReport, report_id, "Service report")
    if report.field_job_id != job_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service report not found")
    return _public(report)


@router.post("/{job_id}/reports", response_model=ServiceReportPublic, status_code=status.HTTP_201_CREATED)
async def create_report(
    job_id: UUID,
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ServiceReportPublic:
    job = _visible_job_or_404(db, job_id, user)
    _can_upload(user, job)
    body = await file.read(s3_svc.MAX_UPLOAD_BYTES + 1)
    key = s3_svc.upload_report_file(job.id, file, body)
    report = ServiceReport(
        field_job_id=job.id,
        file_url=key,
        notes=notes.strip() if notes and notes.strip() else None,
    )
    db.add(report)
    write_audit(
        db,
        actor=user,
        action="create",
        entity_type="service_report",
        entity_id=report.id,
        details={"field_job_id": str(job.id), "s3_key": key, "filename": file.filename},
    )
    try:
        commit_session(db)
    except Exception:
        s3_svc.delete_object(key)
        raise
    db.refresh(report)
    return _public(report)
