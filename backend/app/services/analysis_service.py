"""
Axiom Lens - Analysis service for managing analysis records.
"""
from datetime import datetime, UTC
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Analysis, AuditLog
from app.schemas import AnalysisCreate, AnalysisUpdate, PaginationParams


class AnalysisService:
    """Service for analysis management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_analysis(
        self,
        user_id: str,
        analysis_in: AnalysisCreate,
        target_hash: Optional[str] = None,
    ) -> Analysis:
        """Create a new analysis record."""
        analysis = Analysis(
            id=str(uuid4()),
            user_id=user_id,
            type=analysis_in.type,
            name=analysis_in.name,
            description=analysis_in.description,
            target_path=analysis_in.target_path,
            target_hash=target_hash,
            status="pending",
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
    
    async def get_analysis(self, analysis_id: str, user_id: str) -> Optional[Analysis]:
        """Get analysis by ID (user-scoped)."""
        result = await self.db.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_analysis_by_hash(self, target_hash: str, user_id: str) -> Optional[Analysis]:
        """Get analysis by target hash."""
        result = await self.db.execute(
            select(Analysis).where(
                Analysis.target_hash == target_hash,
                Analysis.user_id == user_id,
            ).order_by(desc(Analysis.created_at))
        )
        return result.scalar_one_or_none()
    
    async def list_analyses(
        self,
        user_id: str,
        params: PaginationParams,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> tuple[Sequence[Analysis], int]:
        """List analyses with pagination and filters."""
        query = select(Analysis).where(Analysis.user_id == user_id)
        
        if type_filter:
            query = query.where(Analysis.type == type_filter)
        if status_filter:
            query = query.where(Analysis.status == status_filter)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(desc(Analysis.created_at))
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return items, total
    
    async def update_analysis(
        self,
        analysis_id: str,
        user_id: str,
        analysis_in: AnalysisUpdate,
    ) -> Optional[Analysis]:
        """Update analysis record."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            return None
        
        update_data = analysis_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(analysis, field, value)
        
        if analysis_in.status == "completed":
            analysis.completed_at = datetime.now(UTC)
        
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
    
    async def delete_analysis(self, analysis_id: str, user_id: str) -> bool:
        """Delete analysis record."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            return False
        
        await self.db.delete(analysis)
        await self.db.commit()
        return True


class AuditService:
    """Service for audit logging."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        event_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log an audit event."""
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        params: Optional[PaginationParams] = None,
    ) -> tuple[Sequence[AuditLog], int]:
        """Get audit logs with pagination and filters."""
        query = select(AuditLog)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        if params:
            query = query.order_by(desc(AuditLog.created_at))
            query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return items, total