from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.lookup import require_farm, require_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models import User, UserRole
from app.schemas.auth import UserPublic
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit import write_audit
from app.services.persist import commit_session

router = APIRouter(prefix="/users", tags=["users"])

admin_only = require_roles(UserRole.ADMIN)
readers = require_roles(UserRole.ADMIN, UserRole.AUDITOR)


def _audit_safe(data: dict[str, Any]) -> dict[str, Any]:
    safe = dict(data)
    safe.pop("password", None)
    if "email" in safe and safe["email"] is not None:
        safe["email"] = str(safe["email"])
    if "role" in safe and safe["role"] is not None:
        safe["role"] = safe["role"].value if hasattr(safe["role"], "value") else str(safe["role"])
    if "farm_id" in safe and safe["farm_id"] is not None:
        safe["farm_id"] = str(safe["farm_id"])
    return safe


@router.get("", response_model=list[UserPublic])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: UserRole | None = None,
    farm_id: UUID | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(readers),
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if role is not None:
        stmt = stmt.where(User.role == role)
    if farm_id is not None:
        stmt = stmt.where(User.farm_id == farm_id)
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(readers),
) -> User:
    return require_user(db, user_id)


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> User:
    if payload.farm_id is not None:
        require_farm(db, payload.farm_id)
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        farm_id=payload.farm_id,
        is_active=payload.is_active,
    )
    db.add(user)
    write_audit(
        db,
        actor=actor,
        action="create",
        entity_type="user",
        entity_id=user.id,
        details=_audit_safe(payload.model_dump(exclude={"password"})),
    )
    commit_session(db)
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> User:
    user = require_user(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("farm_id") is not None:
        require_farm(db, data["farm_id"])
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(user, key, value)
    if password is not None:
        user.hashed_password = hash_password(password)
    write_audit(
        db,
        actor=actor,
        action="update",
        entity_type="user",
        entity_id=user.id,
        details=_audit_safe(payload.model_dump(exclude_unset=True)),
    )
    commit_session(db)
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_only),
) -> Response:
    if actor.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    user = require_user(db, user_id)
    write_audit(
        db,
        actor=actor,
        action="delete",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email},
    )
    db.delete(user)
    commit_session(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
