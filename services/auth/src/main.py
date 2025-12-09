"""Auth Service - handles user authentication with JWT tokens."""

import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .mongodb import mongodb
from .auth_router import router as auth_router

settings = get_settings()

#=============== LOGGING ===============
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
#=======================================

#=============== RATE LIMITING ===============
# Create limiter instance
limiter = Limiter(key_func=get_remote_address)
#=============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting auth service")
    await mongodb.connect()
    yield
    logger.info("Shutting down auth service")
    await mongodb.disconnect()


app = FastAPI(
    title="MeterStream Auth Service",
    description="Authentication service with JWT tokens",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routes
app.include_router(auth_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "status": "running",
        "docs": "/docs",
        "api-calls": "/auth/",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": "auth"}


@app.get("/ready")
async def ready():
    """Readiness probe for Kubernetes."""
    try:
        # Check MongoDB connection
        await mongodb.client.admin.command("ping")
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503
