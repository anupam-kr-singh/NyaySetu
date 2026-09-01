"""NyaySetu FastAPI application (Phase 1: health, auth, RBAC)."""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.db.database import engine

settings = get_settings()

app = FastAPI(
    title="NyaySetu API",
    description=(
        "AI-assisted legal guidance and lawyer consultation backend. "
        "Phase 1 exposes authentication and health only. "
        "This service is informational and is not a substitute for a qualified lawyer."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get(
    "/health/db",
    tags=["Health"],
    summary="Database connectivity probe",
    responses={
        200: {"description": "Database reachable"},
        503: {"description": "Database unreachable"},
    },
)
def health_db() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unreachable"},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "database": "reachable"},
    )
