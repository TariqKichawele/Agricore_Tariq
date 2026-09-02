from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.equipment import router as equipment_router
from app.api.v1.farms import router as farms_router
from app.api.v1.field_jobs import router as field_jobs_router
from app.api.v1.reports import router as reports_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(farms_router)
api_router.include_router(users_router)
api_router.include_router(equipment_router)
api_router.include_router(reports_router)
api_router.include_router(field_jobs_router)
api_router.include_router(audit_logs_router)
api_router.include_router(analytics_router)
