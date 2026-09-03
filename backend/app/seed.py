"""Prairie Crest mock data. Run: python -m app.seed [--reset]"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AuditLog,
    Equipment,
    EquipmentStatus,
    Farm,
    FieldJob,
    JobPriority,
    JobStatus,
    ServiceReport,
    User,
    UserRole,
)
from app.services import analytics as analytics_svc
from app.services.audit import write_audit

STAFF_PASSWORD = "PrairieCrest1!"
HAND_PASSWORD = "ChangeMeHand!"
AUDITOR_PASSWORD = "ChangeMeAuditor!"


def _clear(db: Session) -> None:
    db.execute(delete(ServiceReport))
    db.execute(delete(FieldJob))
    db.execute(delete(Equipment))
    db.execute(delete(AuditLog))
    db.execute(update(User).values(farm_id=None))
    db.execute(update(Farm).values(supervisor_id=None))
    db.execute(delete(Farm))
    db.execute(delete(User))
    db.commit()


def _user(
    email: str,
    full_name: str,
    role: UserRole,
    password: str,
) -> User:
    return User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )


def seed(db: Session, *, reset: bool) -> None:
    if reset:
        _clear(db)

    existing = db.scalar(select(User).where(User.email == "hand@agricore.local"))
    if existing is not None and not reset:
        print("Demo data already present. Re-run with --reset to replace it.")
        return

    admin = _user(
        settings.BOOTSTRAP_ADMIN_EMAIL,
        settings.BOOTSTRAP_ADMIN_NAME,
        UserRole.ADMIN,
        settings.BOOTSTRAP_ADMIN_PASSWORD,
    )
    maya = _user("maya.chen@agricore.local", "Maya Chen", UserRole.ADMIN, STAFF_PASSWORD)
    devon = _user("devon.walsh@agricore.local", "Devon Walsh", UserRole.ADMIN, STAFF_PASSWORD)
    auditor = _user("auditor@agricore.local", "Sam Ledger", UserRole.AUDITOR, AUDITOR_PASSWORD)
    jordan = _user("hand@agricore.local", "Jordan Field", UserRole.FIELD_HAND, HAND_PASSWORD)
    renee = _user("renee.okonkwo@agricore.local", "Renee Okonkwo", UserRole.FIELD_HAND, STAFF_PASSWORD)
    luis = _user("luis.padilla@agricore.local", "Luis Padilla", UserRole.FIELD_HAND, STAFF_PASSWORD)
    priya = _user("priya.shah@agricore.local", "Priya Shah", UserRole.FIELD_HAND, STAFF_PASSWORD)
    db.add_all([admin, maya, devon, auditor, jordan, renee, luis, priya])
    db.flush()

    north = Farm(
        name="North Grain Elevator",
        location_region="Red River Valley",
        capacity=14000,
        supervisor_id=maya.id,
    )
    south = Farm(
        name="South Prairie Site",
        location_region="Sheyenne Flats",
        capacity=8000,
        supervisor_id=devon.id,
    )
    west = Farm(
        name="West River Annex",
        location_region="Missouri Coteau",
        capacity=4500,
        supervisor_id=maya.id,
    )
    willow = Farm(
        name="Willow Creek Elevator",
        location_region="Pembina Escarpment",
        capacity=6200,
        supervisor_id=maya.id,
    )
    heartland = Farm(
        name="Heartland Pump Station",
        location_region="James River",
        capacity=2800,
        supervisor_id=devon.id,
    )
    db.add_all([north, south, west, willow, heartland])
    db.flush()

    jordan.farm_id = north.id
    luis.farm_id = north.id
    renee.farm_id = south.id
    priya.farm_id = willow.id
    maya.farm_id = north.id
    devon.farm_id = south.id
    db.flush()

    idle, in_use, maint, retired = (
        EquipmentStatus.IDLE,
        EquipmentStatus.IN_USE,
        EquipmentStatus.MAINTENANCE,
        EquipmentStatus.RETIRED,
    )

    units = [
        Equipment(
            serial_number="JD-8R-4101",
            model="John Deere 8R",
            status=idle,
            fuel_level=12,
            facility_id=north.id,
            assigned_operator_id=jordan.id,
        ),
        Equipment(
            serial_number="JD-8R-4108",
            model="John Deere 8R",
            status=in_use,
            fuel_level=71,
            facility_id=north.id,
            assigned_operator_id=luis.id,
        ),
        Equipment(
            serial_number="CNH-AF-220",
            model="Case IH Axial-Flow",
            status=in_use,
            fuel_level=64,
            facility_id=south.id,
            assigned_operator_id=jordan.id,
        ),
        Equipment(
            serial_number="CNH-AF-331",
            model="Case IH Axial-Flow",
            status=idle,
            fuel_level=18,
            facility_id=south.id,
            assigned_operator_id=luis.id,
        ),
        Equipment(
            serial_number="JD-S790-11",
            model="John Deere S790",
            status=maint,
            fuel_level=40,
            facility_id=south.id,
            assigned_operator_id=None,
        ),
        Equipment(
            serial_number="VAL-SPRAY-9",
            model="Valley 8000",
            status=maint,
            fuel_level=22,
            facility_id=south.id,
            assigned_operator_id=renee.id,
        ),
        Equipment(
            serial_number="CNH-MAG-55",
            model="Case IH Magnum",
            status=idle,
            fuel_level=88,
            facility_id=south.id,
            assigned_operator_id=renee.id,
        ),
        Equipment(
            serial_number="JD-6M-902",
            model="John Deere 6M",
            status=in_use,
            fuel_level=54,
            facility_id=west.id,
            assigned_operator_id=priya.id,
        ),
        Equipment(
            serial_number="VAL-PIVOT-02",
            model="Valley 8000",
            status=in_use,
            fuel_level=8,
            facility_id=heartland.id,
            assigned_operator_id=renee.id,
        ),
        Equipment(
            serial_number="GHL-PUMP-14",
            model="Gorman-Rupp 14",
            status=idle,
            fuel_level=91,
            facility_id=heartland.id,
            assigned_operator_id=None,
        ),
        Equipment(
            serial_number="GHL-PUMP-15",
            model="Gorman-Rupp 14",
            status=retired,
            fuel_level=0,
            facility_id=heartland.id,
            assigned_operator_id=None,
        ),
        Equipment(
            serial_number="JD-S780-04",
            model="John Deere S790",
            status=idle,
            fuel_level=77,
            facility_id=willow.id,
            assigned_operator_id=priya.id,
        ),
    ]
    db.add_all(units)
    db.flush()
    by_serial = {unit.serial_number: unit for unit in units}

    def job(title: str, priority: JobPriority, status: JobStatus, serial: str, operator: User) -> FieldJob:
        return FieldJob(
            title=title,
            priority=priority,
            status=status,
            equipment_id=by_serial[serial].id,
            operator_id=operator.id,
        )

    jobs = [
        job("Pre-season north tractor check", JobPriority.LOW, JobStatus.COMPLETED, "JD-8R-4101", jordan),
        job("Spring tillage pass — north 8R", JobPriority.MEDIUM, JobStatus.COMPLETED, "JD-8R-4108", luis),
        job("North 8R hydraulic leak", JobPriority.CRITICAL, JobStatus.FAILED, "JD-8R-4101", jordan),
        job("Elevator pump inspection", JobPriority.MEDIUM, JobStatus.IN_PROGRESS, "JD-8R-4101", jordan),
        job("South combine harvest pass", JobPriority.CRITICAL, JobStatus.FAILED, "CNH-AF-220", jordan),
        job("Axial-Flow field trial", JobPriority.MEDIUM, JobStatus.COMPLETED, "CNH-AF-220", jordan),
        job("South AF dust-sensor recal", JobPriority.LOW, JobStatus.COMPLETED, "CNH-AF-331", luis),
        job("South AF rotor wrap", JobPriority.CRITICAL, JobStatus.FAILED, "CNH-AF-331", luis),
        job("S790 header service", JobPriority.LOW, JobStatus.PENDING, "JD-S790-11", renee),
        job("Willow S780 grain sample run", JobPriority.MEDIUM, JobStatus.COMPLETED, "JD-S780-04", priya),
        job("Willow bin-fill coverage", JobPriority.MEDIUM, JobStatus.PENDING, "JD-S780-04", priya),
        job("West annex 6M transport", JobPriority.LOW, JobStatus.IN_PROGRESS, "JD-6M-902", priya),
        job("Heartland pivot nozzle test", JobPriority.MEDIUM, JobStatus.FAILED, "VAL-PIVOT-02", renee),
        job("Magnum idle-hour audit", JobPriority.LOW, JobStatus.COMPLETED, "CNH-MAG-55", renee),
    ]
    db.add_all(jobs)
    db.flush()

    write_audit(
        db,
        actor=admin,
        action="seed",
        entity_type="dataset",
        entity_id=None,
        details={"source": "bin/seed.sh", "farms": 5, "users": 8, "equipment": len(units), "jobs": len(jobs)},
    )
    db.commit()

    farms_n = db.scalar(select(func.count()).select_from(Farm)) or 0
    users_n = db.scalar(select(func.count()).select_from(User)) or 0
    units_n = db.scalar(select(func.count()).select_from(Equipment)) or 0
    jobs_n = db.scalar(select(func.count()).select_from(FieldJob)) or 0
    print("Seeded Prairie Crest Cooperative")
    print(f"  farms={farms_n} users={users_n} equipment={units_n} jobs={jobs_n}")
    print(f"  low-fuel={len(analytics_svc.low_fuel_units(db))}")
    print(f"  co-location={len(analytics_svc.co_located_mismatches(db))}")
    print(f"  maintenance-flags={len(analytics_svc.farms_over_maintenance_threshold(db))}")
    print(f"  reporting-lines (Maya)={len(analytics_svc.reporting_line_hands(db, maya.id))}")
    print("Demo logins:")
    print(f"  admin    {settings.BOOTSTRAP_ADMIN_EMAIL} / {settings.BOOTSTRAP_ADMIN_PASSWORD}")
    print(f"  field    hand@agricore.local / {HAND_PASSWORD}")
    print(f"  auditor  auditor@agricore.local / {AUDITOR_PASSWORD}")
    print(f"  staff    *@agricore.local / {STAFF_PASSWORD}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load Prairie Crest mock data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rows and reload the demo dataset",
    )
    args = parser.parse_args(argv)
    db = SessionLocal()
    try:
        seed(db, reset=args.reset)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
