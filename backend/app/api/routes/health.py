"""
Axiom Lens - Health check and version API routes.
"""
from datetime import datetime, UTC
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.schemas import HealthResponse, VersionResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Health check endpoint with database connectivity test."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/version", response_model=VersionResponse)
async def version_info():
    """Version information endpoint."""
    return VersionResponse(
        name=settings.app_name,
        version=settings.app_version,
        description="AI-assisted Reverse Engineering Analysis Platform",
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """Kubernetes readiness probe endpoint."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}