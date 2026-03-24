from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError
from . import database
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.limiter import limiter
from .core.exception_handlers import (
    http_500_handler,
    integrity_error_handler,
    operational_error_handler,
    validation_error_handler,
)
from .auth import routes as auth_routes
from .routers import transactions, obligations, evaluate, notifications, sessions, audit, categories, goals, budgets, reports, accounts, admin_users
from .jobs.debt_reminder import debt_reminder_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start background jobs on startup, clean up on shutdown."""
    import asyncio
    from sqlalchemy import text
    from .database import AsyncSessionLocal

    # Temporary Auto-Schema Fix: Ensure transaction columns exist
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Checking/Fixing database schema drift...")
            await db.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50)"))
            await db.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS resource_id INTEGER"))
            await db.commit()
            logger.info("Schema check completed.")
        except Exception as e:
            logger.error(f"Auto-schema fix failed: {e}")
            await db.rollback()

    task = asyncio.create_task(debt_reminder_job())
    yield
    task.cancel()


# ── App Factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance Tracker API",
    description="Backend API for Finance Tracker Application",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach the rate limiter state and its 429 exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Global Exception Handlers ─────────────────────────────────────────────────
# Order matters: more specific types must be registered before broader ones.
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, http_500_handler)

# ── CORS Middleware ──────────────────────────────────────────────────────────
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(transactions.router)
app.include_router(obligations.router)
app.include_router(evaluate.router)
app.include_router(notifications.router)
app.include_router(sessions.router)
app.include_router(audit.router)
app.include_router(categories.router)
app.include_router(goals.router)
app.include_router(budgets.router)
app.include_router(reports.router)
app.include_router(accounts.router)
app.include_router(admin_users.router)  # Admin-only endpoints — require_admin enforced per endpoint


@app.get("/")
def read_root():
    return {"message": "Welcome to Finance Tracker API"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(database.get_db)):
    """
    Check if the API and its database connection are alive.
    """
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed (DB Issue): {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "detail": str(e)}
        )
