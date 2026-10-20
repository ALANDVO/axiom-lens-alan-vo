import pytest
from httpx import AsyncClient
from app.models import User, Analysis
from app.core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_analysis(client: AsyncClient, db_session: AsyncSession):
    """Test creating an analysis."""
    # Create a user
    user = User(
        oidc_sub="test-user",
        email="test@example.com",
        name="Test User",
        roles=["operator"],
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create token
    token = create_access_token(
        subject=user.oidc_sub,
        email=user.email,
        name=user.name,
        roles=user.roles,
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "/api/v1/analyses",
        json={
            "type": "binary",
            "name": "Test Binary Analysis",
            "description": "Analyzing a test binary",
            "target_path": "/path/to/binary",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Binary Analysis"
    assert data["type"] == "binary"
    assert data["status"] == "pending"
    assert data["user_id"] == user.oidc_sub


@pytest.mark.asyncio
async def test_create_analysis_invalid_type(client: AsyncClient, db_session: AsyncSession):
    """Test creating analysis with invalid type."""
    user = User(oidc_sub="test-user2", email="test2@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/analyses",
        json={"type": "invalid", "name": "Test"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_analyses(client: AsyncClient, db_session: AsyncSession):
    """Test listing analyses."""
    user = User(oidc_sub="test-user3", email="test3@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    # Create some analyses
    for i in range(3):
        analysis = Analysis(
            user_id=user.oidc_sub,
            type="binary",
            name=f"Analysis {i}",
            status="completed",
        )
        db_session.add(analysis)
    await db_session.commit()
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/analyses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_analyses_pagination(client: AsyncClient, db_session: AsyncSession):
    """Test analysis pagination."""
    user = User(oidc_sub="test-user4", email="test4@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    for i in range(5):
        analysis = Analysis(user_id=user.oidc_sub, type="binary", name=f"Analysis {i}", status="pending")
        db_session.add(analysis)
    await db_session.commit()
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/analyses?page=1&page_size=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_list_analyses_filters(client: AsyncClient, db_session: AsyncSession):
    """Test analysis filtering."""
    user = User(oidc_sub="test-user5", email="test5@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    analysis1 = Analysis(user_id=user.oidc_sub, type="binary", name="Binary 1", status="completed")
    analysis2 = Analysis(user_id=user.oidc_sub, type="javascript", name="JS 1", status="pending")
    analysis3 = Analysis(user_id=user.oidc_sub, type="process", name="Process 1", status="failed")
    db_session.add_all([analysis1, analysis2, analysis3])
    await db_session.commit()
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Filter by type
    response = await client.get("/api/v1/analyses?type_filter=binary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "binary"
    
    # Filter by status
    response = await client.get("/api/v1/analyses?status_filter=completed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_get_analysis(client: AsyncClient, db_session: AsyncSession):
    """Test getting a single analysis."""
    user = User(oidc_sub="test-user6", email="test6@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    analysis = Analysis(
        user_id=user.oidc_sub,
        type="binary",
        name="Get Test",
        status="completed",
        result={"functions": 10},
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(f"/api/v1/analyses/{analysis.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == analysis.id
    assert data["name"] == "Get Test"
    assert data["result"]["functions"] == 10


@pytest.mark.asyncio
async def test_get_analysis_not_found(client: AsyncClient, db_session: AsyncSession):
    """Test getting non-existent analysis."""
    user = User(oidc_sub="test-user7", email="test7@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_analysis(client: AsyncClient, db_session: AsyncSession):
    """Test updating an analysis."""
    user = User(oidc_sub="test-user8", email="test8@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    analysis = Analysis(user_id=user.oidc_sub, type="binary", name="Original", status="pending")
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.patch(
        f"/api/v1/analyses/{analysis.id}",
        json={"name": "Updated", "status": "completed"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_delete_analysis(client: AsyncClient, db_session: AsyncSession):
    """Test deleting an analysis."""
    user = User(oidc_sub="test-user9", email="test9@example.com", roles=["operator"])
    db_session.add(user)
    await db_session.commit()
    
    analysis = Analysis(user_id=user.oidc_sub, type="binary", name="To Delete", status="pending")
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    
    token = create_access_token(subject=user.oidc_sub, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.delete(f"/api/v1/analyses/{analysis.id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deleted
    response = await client.get(f"/api/v1/analyses/{analysis.id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_isolation(client: AsyncClient, db_session: AsyncSession):
    """Test users can only see their own analyses."""
    user1 = User(oidc_sub="user1", email="user1@example.com", roles=["operator"])
    user2 = User(oidc_sub="user2", email="user2@example.com", roles=["operator"])
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    analysis1 = Analysis(user_id=user1.oidc_sub, type="binary", name="User 1 Analysis", status="pending")
    analysis2 = Analysis(user_id=user2.oidc_sub, type="binary", name="User 2 Analysis", status="pending")
    db_session.add_all([analysis1, analysis2])
    await db_session.commit()
    
    token1 = create_access_token(subject=user1.oidc_sub, roles=user1.roles)
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    response = await client.get("/api/v1/analyses", headers=headers1)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "User 1 Analysis"