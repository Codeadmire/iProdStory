"""
FastAPI application entry point.

Initialises:
  - Structured JSON logging (human-readable in dev, JSON lines in production)
  - Sentry (if configured)
  - CORS from config (never wildcard in production)
  - Rate limiting via slowapi
  - Request logging middleware
  - Static media files (local dev only — use CDN/S3 in production)
  - All API routers
  - Auto-creates DB tables (Alembic handles migrations in production)
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from utils.logging import configure_logging, get_logger, RequestLoggingMiddleware
import database
import models

# ── Logging (must be first) ───────────────────────────────────────────────────
configure_logging()
logger = get_logger(__name__)

# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.2)
    logger.info("Sentry initialised")

# ── DB bootstrap (dev shortcut; Alembic owns this in production) ──────────────
models.Base.metadata.create_all(bind=database.engine)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,   # Disable Swagger in prod
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Request logging ───────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Explicitly list allowed origins — never use allow_origins=["*"] in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-Id"],
)

# ── Static media (local dev only) ─────────────────────────────────────────────
_media_path = settings.LOCAL_STORAGE_PATH
if settings.STORAGE_BACKEND == "local":
    os.makedirs(_media_path, exist_ok=True)
    app.mount("/media", StaticFiles(directory=_media_path), name="media")

# ── Routers ───────────────────────────────────────────────────────────────────
from routers.auth_router import router as auth_router
from routers.products import router as products_router
from routers.jobs import router as jobs_router
from routers.linkedin import router as linkedin_router
from routers.crawls import router as crawls_router

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(jobs_router)
app.include_router(linkedin_router)
app.include_router(crawls_router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "env": settings.APP_ENV}


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
