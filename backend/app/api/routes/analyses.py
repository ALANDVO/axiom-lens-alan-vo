"""
Axiom Lens - Analysis API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas import (
    AnalysisCreate,
    AnalysisUpdate,
    AnalysisResponse,
    AnalysisListResponse,
    PaginationParams,
    ErrorResponse,
)
from app.api.dependencies import get_current_user_id, get_db
from app.services.analysis_service import AnalysisService


router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisResponse, status_code=201)
async def create_analysis(
    analysis_in: AnalysisCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new analysis."""
    service = AnalysisService(db)
    analysis = await service.create_analysis(current_user_id, analysis_in)
    return analysis


@router.post("/upload", response_model=AnalysisResponse, status_code=201)
async def create_analysis_with_upload(
    file: UploadFile = File(...),
    type: str = File(...),
    name: str = File(...),
    description: Optional[str] = File(None),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new analysis with file upload."""
    from app.schemas import AnalysisCreate
    analysis_in = AnalysisCreate(type=type, name=name, description=description)
    service = AnalysisService(db)
    analysis = await service.create_analysis_with_upload(current_user_id, analysis_in, file)
    return analysis


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: Optional[str] = Query(None, pattern="^(binary|javascript|process)$"),
    status_filter: Optional[str] = Query(None, pattern="^(pending|running|completed|failed)$"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List analyses with pagination and filters."""
    service = AnalysisService(db)
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await service.list_analyses(
        current_user_id, params, type_filter, status_filter
    )
    
    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis by ID."""
    service = AnalysisService(db)
    analysis = await service.get_analysis(analysis_id, current_user_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.patch("/{analysis_id}", response_model=AnalysisResponse)
async def update_analysis(
    analysis_id: str,
    analysis_in: AnalysisUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update analysis."""
    service = AnalysisService(db)
    analysis = await service.update_analysis(analysis_id, current_user_id, analysis_in)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete analysis."""
    service = AnalysisService(db)
    deleted = await service.delete_analysis(analysis_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")