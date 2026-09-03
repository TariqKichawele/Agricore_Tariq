from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.bootstrap import ensure_bootstrap_admin
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.errors import install_error_handlers

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness probe"},
    {"name": "auth", "description": "JWT login and current-user checks"},
    {"name": "farms", "description": "Member farm sites and grain elevators"},
    {"name": "users", "description": "Co-op accounts. Admin creates users; no public signup"},
    {"name": "equipment", "description": "Shared fleet. Field hands see assigned units only"},
    {"name": "field-jobs", "description": "Work orders. Field hands may PATCH status on their jobs"},
    {"name": "service-reports", "description": "Diagnostic file uploads to private S3"},
    {"name": "analytics", "description": "Operational questions: fuel, co-location, reliability, maintenance, reporting lines"},
    {"name": "audit-logs", "description": "Searchable write-path audit trail (admin and auditor)"},
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AgriCore Command Center API",
    description=(
        "Prairie Crest Agricultural Cooperative farm operations API. "
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)

install_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agricore-api"}
