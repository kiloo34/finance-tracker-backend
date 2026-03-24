"""
Shared pytest fixtures for the FinTrack test suite.

Uses an in-memory SQLite database (via aiosqlite) instead of PostgreSQL so
tests run completely offline and in isolation from production data.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.core.limiter import limiter

# ── Test database ──────────────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


# Override the DB dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db

# ── Rate limiter: reset storage before every test ─────────────────────
# Without this, all requests in the test suite share the same "testclient" IP
# key and trip the rate limit after 5 requests. SlowAPI's .reset() clears
# the in-memory storage so each test starts with a clean limiter state.
@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear SlowAPI's in-memory storage before each test."""
    limiter.reset()
    yield


# ── Session-scoped DB setup / teardown ────────────────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── HTTP client ────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Reusable helpers ───────────────────────────────────────────────────────────
CREDENTIALS = {"username": "testuser_main", "password": "testpassword123"}


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    """Register a fresh test user (idempotent)."""
    res = await client.post("/auth/register", json=CREDENTIALS)
    assert res.status_code in (200, 400)  # 400 = already exists
    return CREDENTIALS


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user):
    """Return Authorization header dict for the test user."""
    res = await client.post(
        "/auth/login",
        data={"username": registered_user["username"], "password": registered_user["password"]},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
