"""
Axiom Lens - Analysis API routes.
"""
from typing import Optional
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.config import settings
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
from app.services.binary_analyzer import analyze_binary


router = APIRouter(prefix="/analyses", tags=["analyses"])


UPLOAD_DIR = Path(settings.database_url.replace("sqlite+aiosqlite:///", "")).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def compute_file_hash(file: UploadFile) -> tuple[str, Path]:
    """Compute SHA256 hash of uploaded file and save it."""
    hasher = hashlib.sha256()
    file_path = UPLOAD_DIR / file.filename
    content = await file.read()
    hasher.update(content)
    file_path.write_bytes(content)
    await file.seek(0)
    return hasher.hexdigest(), file_path


async def run_binary_analysis(analysis_id: str, file_path: Path, user_id: str, db_factory) -> None:
    """Background task to run binary analysis and update results."""
    try:
        # Analyze the binary
        results = analyze_binary(file_path)
        
        # Update analysis with results
        async with db_factory() as db:
            service = AnalysisService(db)
            await service.update_analysis(
                analysis_id,
                user_id,
                AnalysisUpdate(
                    status="completed",
                    result=results,
                )
            )
    except Exception as e:
        # Update analysis with error
        async with db_factory() as db:
            service = AnalysisService(db)
            await service.update_analysis(
                analysis_id,
                user_id,
                AnalysisUpdate(
                    status="failed",
                    error=str(e),
                )
            )


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
async def upload_binary(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_analyze: bool = True,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a binary file for analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Compute hash and save file
    target_hash, file_path = await compute_file_hash(file)
    
    # Check if analysis already exists for this hash
    service = AnalysisService(db)
    existing = await service.get_analysis_by_hash(target_hash, current_user_id)
    if existing:
        return existing
    
    # Create analysis record
    analysis_name = name or file.filename
    analysis_in = AnalysisCreate(
        type="binary",
        name=analysis_name,
        description=description,
        target_path=str(file_path),
    )
    analysis = await service.create_analysis(current_user_id, analysis_in, target_hash=target_hash)
    
    # Schedule background analysis if requested
    if auto_analyze:
        from app.core.database import AsyncSessionLocal
        background_tasks.add_task(
            run_binary_analysis,
            analysis.id,
            file_path,
            current_user_id,
            AsyncSessionLocal,
        )
        # Update status to running
        await service.update_analysis(
            analysis.id,
            current_user_id,
            AnalysisUpdate(status="running"),
        )
        # Refresh to get updated status
        await db.refresh(analysis)
    
    return analysis


@router.post("/{analysis_id}/analyze", response_model=AnalysisResponse, status_code=202)
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger analysis for an existing analysis record."""
    service = AnalysisService(db)
    analysis = await service.get_analysis(analysis_id, current_user_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis.type != "binary":
        raise HTTPException(status_code=400, detail="Only binary analysis is supported")
    
    if not analysis.target_path:
        raise HTTPException(status_code=400, detail="No target file associated with this analysis")
    
    file_path = Path(analysis.target_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Target file not found")
    
    # Update status to running
    await service.update_analysis(
        analysis_id,
        current_user_id,
        AnalysisUpdate(status="running"),
    )
    
    # Schedule background analysis
    from app.core.database import AsyncSessionLocal
    background_tasks.add_task(
        run_binary_analysis,
        analysis_id,
        file_path,
        current_user_id,
        AsyncSessionLocal,
    )
    
    # Return updated analysis
    await db.refresh(analysis)
    return analysis


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, alias="search"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List analyses with pagination and filters."""
    service = AnalysisService(db)
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await service.list_analyses(
        current_user_id,
        params,
        type_filter=type_filter,
        status_filter=status_filter,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size
    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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
