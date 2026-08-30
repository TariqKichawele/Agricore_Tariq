from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Equipment, Farm, FieldJob, User, UserRole

T = TypeVar("T")


def get_or_404(db: Session, model: type[T], entity_id: UUID, label: str) -> T:
    obj = db.get(model, entity_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


def require_farm(db: Session, farm_id: UUID) -> Farm:
    return get_or_404(db, Farm, farm_id, "Farm")


def require_user(db: Session, user_id: UUID) -> User:
    return get_or_404(db, User, user_id, "User")


def require_equipment(db: Session, equipment_id: UUID) -> Equipment:
    return get_or_404(db, Equipment, equipment_id, "Equipment")


def require_field_job(db: Session, job_id: UUID) -> FieldJob:
    return get_or_404(db, FieldJob, job_id, "Field job")


def require_field_hand(db: Session, user_id: UUID) -> User:
    user = require_user(db, user_id)
    if user.role != UserRole.FIELD_HAND:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operator must be a field hand",
        )
    return user
