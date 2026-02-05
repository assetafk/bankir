import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import accounts, admin, auth, transfers, transactions
from app.config import settings
from app.core.request_id import RequestIDMiddleware
from app.core.security_middleware import (
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.xss_middleware import XSSProtectionMiddleware
from app.database import Base, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request ID middleware - Add first to track all requests
app.add_middleware(RequestIDMiddleware)

# XSS Protection middleware - Add early to validate all inputs
app.add_middleware(XSSProtectionMiddleware)

# Security middleware - Add third to apply security headers to all requests
app.add_middleware(SecurityHeadersMiddleware)

# HTTPS redirect middleware (optional, enable in production)
if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)
    app.state.force_https = True

# CORS middleware with secure configuration
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "X-Requested-With"],
    expose_headers=["Content-Type", "X-Request-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

# Serve static files from frontend build (if exists)
# Frontend is at the same level as backend directory
_frontend_root = os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))
)
frontend_dist = os.path.join(_frontend_root, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Root: redirect to docs when no static frontend is mounted
@app.get("/")
async def root():
    """Redirect to API docs when opening backend root."""
    return RedirectResponse(url="/docs", status_code=302)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup and verify connectivity (warms Neon on first request)."""
    logger.info("Starting up Banking Service...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except Exception as e:
        logger.error("Database connection failed at startup: %s", e)
        raise
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Banking Service...")
