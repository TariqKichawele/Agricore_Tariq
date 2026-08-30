from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.lookup import require_equipment, require_farm, require_field_hand
from app.core.database import get_db
from app.models import Equipment, EquipmentStatus, User, UserRole
from app.schemas.equipment import EquipmentCreate, EquipmentPublic, EquipmentUpdate
from app.services.audit import write_audit
from app.services.persist import commit_session

router = APIRouter(prefix="/equipment", tags=["equipment"])

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


def _apply_equipment_refs(db: Session, payload: dict[str, Any]) -> None:
    if payload.get("facility_id") is not None:
        require_farm(db, payload["facility_id"])
    if payload.get("assigned_operator_id") is not None:
        require_field_hand(db, payload["assigned_operator_id"])


@router.get("", response_model=list[EquipmentPublic])
def list_equipment(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    facility_id: UUID | None = None,
    status_filter: EquipmentStatus | None = Query(default=None, alias="status"),
    assigned_operator_id: UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Equipment]:
    stmt = select(Equipment).order_by(Equipment.created_at.desc())
    if user.role == UserRole.FIELD_HAND:
        stmt = stmt.where(Equipment.assigned_operator_id == user.id)
    elif user.role not in (UserRole.ADMIN, UserRole.AUDITOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if facility_id is not None:
        stmt = stmt.where(Equipment.facility_id == facility_id)
    if status_filter is not None:
        stmt = stmt.where(Equipment.status == status_filter)
    if assigned_operator_id is not None:
        if user.role == UserRole.FIELD_HAND and assigned_operator_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        stmt = stmt.where(Equipment.assigned_operator_id == assigned_operator_id)
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())


@router.get("/{equipment_id}", response_model=EquipmentPublic)
def get_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Equipment:
    unit = require_equipment(db, equipment_id)
    if user.role == UserRole.FIELD_HAND and unit.assigned_operator_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if user.role not in (UserRole.ADMIN, UserRole.AUDITOR, UserRole.FIELD_HAND):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return unit


@router.post("", response_model=EquipmentPublic, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Equipment:
    data = payload.model_dump()
    _apply_equipment_refs(db, data)
    unit = Equipment(**data)
    db.add(unit)
    write_audit(
        db,
        actor=actor,
        action="create",
        entity_type="equipment",
        entity_id=unit.id,
        details=_jsonable({"serial_number": unit.serial_number, "model": unit.model, "facility_id": unit.facility_id}),
    )
    commit_session(db)
    db.refresh(unit)
    return unit


@router.patch("/{equipment_id}", response_model=EquipmentPublic)
def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Equipment:
    unit = require_equipment(db, equipment_id)
    data = payload.model_dump(exclude_unset=True)
    _apply_equipment_refs(db, data)
    for key, value in data.items():
        setattr(unit, key, value)
    write_audit(
        db,
        actor=actor,
        action="update",
        entity_type="equipment",
        entity_id=unit.id,
        details=_jsonable(data),
    )
    commit_session(db)
    db.refresh(unit)
    return unit


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Response:
    unit = require_equipment(db, equipment_id)
    write_audit(
        db,
        actor=actor,
        action="delete",
        entity_type="equipment",
        entity_id=unit.id,
        details={"serial_number": unit.serial_number},
    )
    db.delete(unit)
    commit_session(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
