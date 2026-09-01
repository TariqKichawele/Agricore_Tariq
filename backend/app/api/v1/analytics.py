from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.lookup import require_user
from app.core.database import get_db
from app.models import User
from app.schemas.analytics import (
    CoLocationItem,
    CoLocationResponse,
    LowFuelItem,
    LowFuelResponse,
    MaintenanceFlagItem,
    MaintenanceFlagsResponse,
    ReliabilityResponse,
    ReliabilityRow,
    ReportingLinesResponse,
)
from app.services import analytics as analytics_svc

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/low-fuel", response_model=LowFuelResponse)
def get_low_fuel(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> LowFuelResponse:
    items = analytics_svc.low_fuel_units(db)
    return LowFuelResponse(count=len(items), items=[LowFuelItem.model_validate(unit) for unit in items])


@router.get("/co-location", response_model=CoLocationResponse)
def get_co_location(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CoLocationResponse:
    rows = analytics_svc.co_located_mismatches(db)
    items = [
        CoLocationItem(
            equipment_id=unit.id,
            serial_number=unit.serial_number,
            model=unit.model,
            facility_id=unit.facility_id,
            assigned_operator_id=operator_id,
            operator_farm_id=operator_farm_id,
        )
        for unit, operator_farm_id in rows
        if (operator_id := unit.assigned_operator_id) is not None
    ]
    return CoLocationResponse(count=len(items), items=items)


@router.get("/reliability", response_model=ReliabilityResponse)
def get_reliability(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ReliabilityResponse:
    rows = analytics_svc.reliability_by_model(db)
    return ReliabilityResponse(
        models=[ReliabilityRow(model=model, completed=completed, failed=failed) for model, completed, failed in rows]
    )


@router.get("/maintenance-flags", response_model=MaintenanceFlagsResponse)
def get_maintenance_flags(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> MaintenanceFlagsResponse:
    rows = analytics_svc.farms_over_maintenance_threshold(db)
    farms = [
        MaintenanceFlagItem(
            farm=farm,
            unit_count=unit_count,
            maintenance_count=maintenance_count,
            maintenance_ratio=round(ratio, 4),
        )
        for farm, unit_count, maintenance_count, ratio in rows
    ]
    return MaintenanceFlagsResponse(count=len(farms), farms=farms)


@router.get("/reporting-lines", response_model=ReportingLinesResponse)
def get_reporting_lines(
    supervisor_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ReportingLinesResponse:
    require_user(db, supervisor_id)
    hands = analytics_svc.reporting_line_hands(db, supervisor_id)
    return ReportingLinesResponse(count=len(hands), field_hands=hands)
