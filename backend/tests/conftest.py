from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
import app.models as _all_models  # Ensure all model tables are registered in Base.metadata
from app.models.user import User
from app.core.security import get_password_hash, create_access_token

# In-memory SQLite with StaticPool so all async sessions share the exact same clean state
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def init_test_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test and drop them afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_celery_delay():
    """Mock Celery task.delay to prevent network calls to Redis in unit/integration tests."""
    with patch("app.services.document_service.process_document_task.delay") as mock_delay:
        mock_delay.return_value = MagicMock(id="mock-task-id")
        yield mock_delay


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """FastAPI async test client with overridden DB session."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user() -> User:
    """Fixture creating a verified active test user."""
    async with TestingSessionLocal() as session:
        user = User(
            email="testuser@example.com",
            password_hash=get_password_hash("ValidPass123!"),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
def user_token(test_user: User) -> str:
    """JWT Bearer token for test_user."""
    return create_access_token(subject=str(test_user.id))


@pytest_asyncio.fixture
def auth_headers(user_token: str) -> dict[str, str]:
    """HTTP Authorization headers for test_user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
async def admin_user() -> User:
    """Fixture creating an admin user."""
    async with TestingSessionLocal() as session:
        admin = User(
            email="admin_knowledge_36@knowledge.ai",
            password_hash=get_password_hash("Test!234"),
            is_active=True,
            is_superuser=True,
            role="admin",
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


@pytest_asyncio.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """HTTP Authorization headers for admin_user."""
    token = create_access_token(subject=str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}

