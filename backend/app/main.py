from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.bootstrap import ensure_bootstrap_admin
from app.core.config import settings
from app.core.database import SessionLocal

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
    description="Prairie Crest Agricultural Cooperative farm operations API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agricore-api"}
