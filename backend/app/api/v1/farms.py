from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.lookup import require_farm, require_user
from app.core.database import get_db
from app.models import Farm, User, UserRole
from app.schemas.farm import FarmCreate, FarmPublic, FarmUpdate
from app.services.audit import write_audit
from app.services.persist import commit_session

router = APIRouter(prefix="/farms", tags=["farms"])

admin_only = require_roles(UserRole.ADMIN)
readers = require_roles(UserRole.ADMIN, UserRole.AUDITOR)


def _apply_farm_refs(db: Session, payload: dict[str, Any]) -> None:
    if "supervisor_id" in payload and payload["supervisor_id"] is not None:
        require_user(db, payload["supervisor_id"])


@router.get("", response_model=list[FarmPublic])
def list_farms(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(readers),
) -> list[Farm]:
    return list(db.scalars(select(Farm).order_by(Farm.created_at.desc()).offset(skip).limit(limit)).all())


@router.get("/{farm_id}", response_model=FarmPublic)
def get_farm(
    farm_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(readers),
) -> Farm:
    return require_farm(db, farm_id)


@router.post("", response_model=FarmPublic, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Farm:
    data = payload.model_dump()
    _apply_farm_refs(db, data)
    farm = Farm(**data)
    db.add(farm)
    write_audit(
        db,
        actor=actor,
        action="create",
        entity_type="farm",
        entity_id=farm.id,
        details={"name": farm.name, "location_region": farm.location_region},
    )
    commit_session(db)
    db.refresh(farm)
    return farm


@router.patch("/{farm_id}", response_model=FarmPublic)
def update_farm(
    farm_id: UUID,
    payload: FarmUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Farm:
    farm = require_farm(db, farm_id)
    data = payload.model_dump(exclude_unset=True)
    _apply_farm_refs(db, data)
    for key, value in data.items():
        setattr(farm, key, value)
    write_audit(
        db,
        actor=actor,
        action="update",
        entity_type="farm",
        entity_id=farm.id,
        details=data,
    )
    commit_session(db)
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Response:
    farm = require_farm(db, farm_id)
    write_audit(
        db,
        actor=actor,
        action="delete",
        entity_type="farm",
        entity_id=farm.id,
        details={"name": farm.name},
    )
    db.delete(farm)
    commit_session(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
