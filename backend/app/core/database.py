"""
database.py — Async SQLAlchemy engine, session factory, and dependency injector.

Design decisions:
- Uses `create_async_engine` with the asyncpg driver for non-blocking I/O.
- `AsyncSession` is the session class; all DB calls must be awaited.
- `get_db` is a FastAPI dependency that yields a session per request and
  guarantees rollback on exception and close on exit (even in error paths).
- The `Base` declarative base lives here so all models can import from one place.
- `init_db()` is a lightweight startup check (not a migration tool — use Alembic).
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Declarative Base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    All table models must inherit from this class so that Alembic's
    `autogenerate` can discover them automatically.
    """
    pass


# ── Engine ────────────────────────────────────────────────────────────────────

def _build_engine() -> AsyncEngine:
    """
    Construct the async SQLAlchemy engine.

    Pool strategy:
      - In production, use QueuePool (default) with pool_size / max_overflow.
      - In testing, NullPool is typically preferred (one connection per test).
        Override DATABASE_URL env var and set ENVIRONMENT=testing to switch.
    """
    connect_args: dict = {
        # asyncpg-specific options
        "server_settings": {
            "application_name": settings.APP_NAME,
            # Force UTC on every connection — prevents timezone bugs
            "TimeZone": "UTC",
        },
        "command_timeout": 60,
    }

    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.DEBUG,           # logs all SQL when DEBUG=True
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,            # detect stale connections before use
        connect_args=connect_args,
    )

    logger.info(
        "Async SQLAlchemy engine created | host=%s db=%s pool_size=%d",
        settings.DATABASE_HOST,
        settings.DATABASE_NAME,
        settings.DB_POOL_SIZE,
    )
    return engine


engine: AsyncEngine = _build_engine()


# ── Session Factory ───────────────────────────────────────────────────────────

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep attributes accessible after commit
    autocommit=False,
    autoflush=False,
)


# ── FastAPI Dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a transactional async DB session.

    Usage:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically:
      - Committed on successful exit.
      - Rolled back on any unhandled exception.
      - Closed in the finally block regardless of outcome.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.exception("Database error — transaction rolled back: %s", exc)
            raise
        except Exception as exc:
            await session.rollback()
            logger.exception("Unexpected error — transaction rolled back: %s", exc)
            raise
        finally:
            await session.close()


# ── Startup / Shutdown Helpers ────────────────────────────────────────────────

async def init_db() -> None:
    """
    Verify the database connection on application startup.

    This does NOT run migrations or create tables — use Alembic for that.
    It simply opens a connection to confirm the engine is reachable and the
    credentials are valid, then closes it immediately.
    """
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified successfully.")
    except Exception as exc:
        logger.critical(
            "❌ Cannot connect to the database at startup: %s", exc
        )
        raise


async def close_db() -> None:
    """
    Gracefully dispose of the connection pool on application shutdown.

    Call this from the FastAPI `lifespan` shutdown handler to allow
    in-flight queries to complete before the process exits.
    """
    await engine.dispose()
    logger.info("Database connection pool disposed.")
