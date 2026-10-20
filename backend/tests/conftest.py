import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_db_session
from app.core.config import Settings

# Import models to register with Base.metadata
from app import models
import tempfile
import os

# Test database - use file-based for proper sharing between connections
test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
os.close(test_db_fd)
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{test_db_path}"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # Ensure models are imported and registered with Base.metadata
    import app.models
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()
    try:
        os.unlink(test_db_path)
    except OSError:
        pass


@pytest.fixture
async def db_session():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def client(db_session):
    # Override settings for test - non-demo mode for API tests
    from app.core.config import settings
    settings.demo_mode = False
    settings.environment = "development"
    settings.oidc_enabled = False
    
    # Ensure models are imported
    import app.models
    
    app = create_app()
    
    from app.api.dependencies import get_db
    from app.core.database import get_db_session
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    # Also override get_db_session for any direct uses
    async def override_get_db_session():
        yield db_session
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def demo_client(db_session):
    # Override settings for test - demo mode for auth tests
    from app.core.config import settings
    settings.demo_mode = True
    settings.environment = "development"
    settings.oidc_enabled = True
    
    # Ensure models are imported
    import app.models
    
    app = create_app()
    
    from app.api.dependencies import get_db
    from app.core.database import get_db_session
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    # Also override get_db_session for any direct uses
    async def override_get_db_session():
        yield db_session
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    return Settings(
        environment="development",
        debug=True,
        secret_key="test-secret-key-for-testing-min-32-chars",
        demo_mode=True,
        oidc_enabled=False,
    )