from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import EquipmentStatus, JobPriority, JobStatus, UserRole


def _str_enum(enum_cls: type, name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        length=32,
        values_callable=lambda members: [item.value for item in members],
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(_str_enum(UserRole, "user_role"), nullable=False)
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    home_farm: Mapped[Farm | None] = relationship(
        foreign_keys="User.farm_id",
        back_populates="members",
    )
    supervised_farms: Mapped[list[Farm]] = relationship(
        foreign_keys="Farm.supervisor_id",
        back_populates="supervisor",
    )
    assigned_equipment: Mapped[list[Equipment]] = relationship(
        back_populates="assigned_operator",
    )
    field_jobs: Mapped[list[FieldJob]] = relationship(back_populates="operator")
    audit_entries: Mapped[list[AuditLog]] = relationship(back_populates="actor")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_region: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_farms_supervisor_id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    supervisor: Mapped[User | None] = relationship(
        foreign_keys="Farm.supervisor_id",
        back_populates="supervised_farms",
    )
    members: Mapped[list[User]] = relationship(
        foreign_keys="User.farm_id",
        back_populates="home_farm",
    )
    equipment_units: Mapped[list[Equipment]] = relationship(back_populates="facility")


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("fuel_level >= 0 AND fuel_level <= 100", name="ck_equipment_fuel_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[EquipmentStatus] = mapped_column(
        _str_enum(EquipmentStatus, "equipment_status"),
        nullable=False,
        default=EquipmentStatus.IDLE,
    )
    fuel_level: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_operator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    facility: Mapped[Farm] = relationship(back_populates="equipment_units")
    assigned_operator: Mapped[User | None] = relationship(back_populates="assigned_equipment")
    field_jobs: Mapped[list[FieldJob]] = relationship(back_populates="equipment")


class FieldJob(Base):
    __tablename__ = "field_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[JobPriority] = mapped_column(
        _str_enum(JobPriority, "job_priority"),
        nullable=False,
        default=JobPriority.MEDIUM,
    )
    status: Mapped[JobStatus] = mapped_column(
        _str_enum(JobStatus, "job_status"),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    operator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    equipment: Mapped[Equipment] = relationship(back_populates="field_jobs")
    operator: Mapped[User] = relationship(back_populates="field_jobs")
    service_reports: Mapped[list[ServiceReport]] = relationship(back_populates="field_job")


class ServiceReport(Base):
    __tablename__ = "service_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    field_job: Mapped[FieldJob] = relationship(back_populates="service_reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor: Mapped[User | None] = relationship(back_populates="audit_entries")
