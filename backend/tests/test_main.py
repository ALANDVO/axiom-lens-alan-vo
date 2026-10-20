import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_version_info(client: AsyncClient):
    """Test version info endpoint."""
    response = await client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Axiom Lens"
    assert "version" in data
    assert "description" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness probe."""
    response = await client.get("/api/v1/ready")
    assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness probe."""
    response = await client.get("/api/v1/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"