import pytest
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Analysis, AuditLog, SessionRecord
from app.services.user_service import UserService
from app.services.analysis_service import AnalysisService, AuditService
from app.schemas import PaginationParams
from app.core.oidc import TokenData

@pytest.mark.asyncio
async def test_user_model(db_session: AsyncSession):
    """Test User model CRUD."""
    user = User(
        oidc_sub="test-sub",
        email="test@example.com",
        name="Test User",
        roles=["viewer"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.oidc_sub == "test-sub"
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_analysis_model(db_session: AsyncSession):
    """Test Analysis model CRUD."""
    user = User(oidc_sub="test-sub2", email="test2@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    analysis = Analysis(
        user_id=user.id,
        type="binary",
        name="Test Analysis",
        description="Description",
        target_path="/path/to/binary",
        target_hash="abc123",
        status="pending",
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    
    assert analysis.id is not None
    assert analysis.user_id == user.id
    assert analysis.status == "pending"
    assert analysis.result is None


@pytest.mark.asyncio
async def test_audit_log_model(db_session: AsyncSession):
    """Test AuditLog model."""
    user = User(oidc_sub="test-sub3", email="test3@example.com")
    db_session.add(user)
    await db_session.commit()
    
    audit = AuditLog(
        user_id=user.id,
        event_type="login",
        event_data={"ip": "127.0.0.1"},
        ip_address="127.0.0.1",
        user_agent="test-agent",
        success=True,
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)
    
    assert audit.id is not None
    assert audit.event_type == "login"
    assert audit.success is True


@pytest.mark.asyncio
async def test_user_service_get_or_create(db_session: AsyncSession):
    """Test UserService get_or_create_user."""
    service = UserService(db_session)
    
    token_data = TokenData(
        sub="new-user",
        email="new@example.com",
        name="New User",
        roles=["viewer"],
        exp=9999999999,
        iat=1000000000,
        jti="test-jti",
    )
    
    # Create new user
    user = await service.get_or_create_user(token_data)
    assert user.oidc_sub == "new-user"
    assert user.email == "new@example.com"
    assert user.name == "New User"
    assert user.roles == ["viewer"]
    
    # Get existing user (should update)
    token_data2 = TokenData(
        sub="new-user",
        email="updated@example.com",
        name="Updated User",
        roles=["operator"],
        exp=9999999999,
        iat=1000000000,
        jti="test-jti-2",
    )
    user2 = await service.get_or_create_user(token_data2)
    assert user2.id == user.id
    assert user2.email == "updated@example.com"
    assert user2.name == "Updated User"
    assert user2.roles == ["operator"]


@pytest.mark.asyncio
async def test_analysis_service(db_session: AsyncSession):
    """Test AnalysisService CRUD."""
    user = User(oidc_sub="service-user", email="service@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    service = AnalysisService(db_session)
    
    # Create
    from app.schemas import AnalysisCreate
    analysis_in = AnalysisCreate(type="binary", name="Service Test", description="Desc")
    analysis = await service.create_analysis(user.id, analysis_in, target_hash="hash123")
    assert analysis.name == "Service Test"
    assert analysis.target_hash == "hash123"
    
    # Get
    fetched = await service.get_analysis(analysis.id, user.id)
    assert fetched is not None
    assert fetched.id == analysis.id
    
    # List
    items, total = await service.list_analyses(user.id, PaginationParams(page=1, page_size=10))
    assert total == 1
    assert len(items) == 1
    
    # Update
    from app.schemas import AnalysisUpdate
    updated = await service.update_analysis(analysis.id, user.id, AnalysisUpdate(name="Updated", status="completed"))
    assert updated.name == "Updated"
    assert updated.status == "completed"
    assert updated.completed_at is not None
    
    # Delete
    deleted = await service.delete_analysis(analysis.id, user.id)
    assert deleted is True
    
    # Verify deleted
    fetched = await service.get_analysis(analysis.id, user.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_audit_service(db_session: AsyncSession):
    """Test AuditService."""
    user = User(oidc_sub="audit-user", email="audit@example.com")
    db_session.add(user)
    await db_session.commit()
    
    service = AuditService(db_session)
    
    # Log event
    audit = await service.log_event(
        event_type="test_event",
        user_id=user.id,
        event_data={"key": "value"},
        ip_address="127.0.0.1",
        success=True,
    )
    assert audit.event_type == "test_event"
    assert audit.success is True
    
    # Get logs
    items, total = await service.get_audit_logs(user_id=user.id, params=PaginationParams(page=1, page_size=10))
    assert total == 1
    assert len(items) == 1