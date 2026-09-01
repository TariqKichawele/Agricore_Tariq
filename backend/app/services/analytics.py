from uuid import UUID

from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.orm import Session

from app.models import Equipment, EquipmentStatus, Farm, FieldJob, JobStatus, User, UserRole

LOW_FUEL_THRESHOLD = 20
ACTIVE_EQUIPMENT_STATUSES = (EquipmentStatus.IDLE, EquipmentStatus.IN_USE)
ACTIVE_JOB_STATUSES = (JobStatus.PENDING, JobStatus.IN_PROGRESS)
MAINTENANCE_RATIO_THRESHOLD = 0.30


def low_fuel_units(db: Session) -> list[Equipment]:
    stmt = (
        select(Equipment)
        .where(
            Equipment.status.in_(ACTIVE_EQUIPMENT_STATUSES),
            Equipment.fuel_level < LOW_FUEL_THRESHOLD,
        )
        .order_by(Equipment.fuel_level.asc(), Equipment.serial_number.asc())
    )
    return list(db.scalars(stmt).all())


def co_located_mismatches(db: Session) -> list[tuple[Equipment, UUID | None]]:
    stmt = (
        select(Equipment, User.farm_id)
        .join(User, Equipment.assigned_operator_id == User.id)
        .where(User.farm_id.is_distinct_from(Equipment.facility_id))
        .order_by(Equipment.serial_number.asc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def reliability_by_model(db: Session) -> list[tuple[str, int, int]]:
    completed = func.coalesce(
        func.sum(case((FieldJob.status == JobStatus.COMPLETED, 1), else_=0)),
        0,
    )
    failed = func.coalesce(
        func.sum(case((FieldJob.status == JobStatus.FAILED, 1), else_=0)),
        0,
    )
    stmt = (
        select(Equipment.model, completed.label("completed"), failed.label("failed"))
        .join(FieldJob, FieldJob.equipment_id == Equipment.id)
        .group_by(Equipment.model)
        .having((completed + failed) > 0)
        .order_by(Equipment.model.asc())
    )
    return [(row.model, int(row.completed), int(row.failed)) for row in db.execute(stmt).all()]


def farms_over_maintenance_threshold(db: Session) -> list[tuple[Farm, int, int, float]]:
    unit_count = func.count(Equipment.id)
    maintenance_count = func.coalesce(
        func.sum(case((Equipment.status == EquipmentStatus.MAINTENANCE, 1), else_=0)),
        0,
    )
    ratio = cast(maintenance_count, Float) / cast(unit_count, Float)
    stmt = (
        select(
            Farm,
            unit_count.label("unit_count"),
            maintenance_count.label("maintenance_count"),
            ratio.label("maintenance_ratio"),
        )
        .join(Equipment, Equipment.facility_id == Farm.id)
        .group_by(Farm.id)
        .having(unit_count > 0, ratio > MAINTENANCE_RATIO_THRESHOLD)
        .order_by(ratio.desc(), Farm.name.asc())
    )
    return [
        (row[0], int(row.unit_count), int(row.maintenance_count), float(row.maintenance_ratio))
        for row in db.execute(stmt).all()
    ]


def reporting_line_hands(db: Session, supervisor_id: UUID) -> list[User]:
    stmt = (
        select(User)
        .join(Farm, User.farm_id == Farm.id)
        .join(FieldJob, FieldJob.operator_id == User.id)
        .where(
            Farm.supervisor_id == supervisor_id,
            User.role == UserRole.FIELD_HAND,
            FieldJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .distinct()
        .order_by(User.full_name.asc())
    )
    return list(db.scalars(stmt).all())
