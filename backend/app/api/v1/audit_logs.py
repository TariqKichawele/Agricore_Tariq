from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import AuditLog, User, UserRole
from app.schemas.audit import AuditLogPublic

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

readers = require_roles(UserRole.ADMIN, UserRole.AUDITOR)


@router.get("", response_model=list[AuditLogPublic])
def list_audit_logs(
    q: str | None = Query(default=None, min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(readers),
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                AuditLog.action.ilike(pattern),
                AuditLog.entity_type.ilike(pattern),
                cast(AuditLog.details, String).ilike(pattern),
            )
        )
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())
