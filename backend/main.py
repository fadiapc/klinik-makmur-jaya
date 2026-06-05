"""
main.py — FastAPI application entry point.

Lifecycle:
  startup  → verify DB connection, initialise Redis, setup logging
  shutdown → dispose DB pool gracefully

All routers will be registered here under /api/v1/.
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import auth_routes, dashboard_routes, order_routes, product_routes, user_routes, audit_routes, setting_routes
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.security import limiter

# ── Logging setup ─────────────────────────────────────────────────────────────

LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "logging.Formatter",
            "fmt": '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if settings.DEBUG else "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    logger.info("🚀 Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    # Ensure upload directory exists at startup
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    (upload_path / "products").mkdir(exist_ok=True)
    logger.info("Upload directory ready: %s", upload_path.resolve())

    # Startup: verify database
    await init_db()

    yield  # ← application runs here

    # Shutdown: release resources
    await close_db()
    logger.info("👋 Application shutdown complete.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
# Bind the shared limiter singleton (defined in security.py) to application state
# so slowapi's middleware can locate it for every request.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["klinikmakmurjaya.id", "*.klinikmakmurjaya.id"],
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Application health check")
async def health_check() -> dict:
    """Returns 200 OK when the application is running."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ── Static files (uploaded images served at /static/<path>) ──────────────────
# Mount AFTER app creation but BEFORE routers so static paths don't shadow API routes.
app.mount(
    "/static",
    StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False),
    name="static",
)

# ── Routers ───────────────────────────────────────────────────────────────────

# Auth & Security module (PRD Section 4.1)
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(user_routes.router, prefix="/api/v1")

# Products management module (PRD Sections 4.3 & 4.5)
app.include_router(product_routes.router, prefix="/api/v1")

# Orders & Prescriptions module (PRD Section 4.4)
app.include_router(order_routes.router, prefix="/api/v1")

# Dashboard & Reporting (Real-time and Background Tasks)
app.include_router(dashboard_routes.router, prefix="/api/v1")
app.include_router(dashboard_routes.ws_router)

# Audit Log (Admin only)
app.include_router(audit_routes.router, prefix="/api/v1")
app.include_router(setting_routes.router, prefix="/api/v1")

# Future routers (added per phase):
# from app.api.v1 import stock_routes
# app.include_router(stock_routes.router, prefix="/api/v1")

# Trigger reload
