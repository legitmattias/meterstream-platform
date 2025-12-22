"""API Gateway - JWT validation and request proxying to backend services.

Notes on analytics integration:
- Adds `/api/data/{path}` routes that proxy to the Queries service.
- Applies global CORS middleware; preflight (OPTIONS) and all responses include CORS headers.
- Proxies to Queries using corrected URLs: `.../api/data/{path}`.
- Supports a dev toggle (`DISABLE_AUTH_FOR_DATA`) to bypass JWT on data routes,
  forwarding `X-Customer-ID` from the client or `DEV_CUSTOMER_ID` when provided.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .config import settings
from .middleware import TokenPayload, validate_jwt

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - handles startup and shutdown."""
    logger.info("Starting API Gateway")
    _app.state.http_client = httpx.AsyncClient(timeout=30.0)
    yield
    logger.info("Shutting down API Gateway")
    await _app.state.http_client.aclose()


app = FastAPI(
    title="API Gateway",
    description="JWT validation and request routing to backend services",
    version="0.1.0",
    lifespan=lifespan,
)

# Global CORS middleware so all responses (incl. 404/500) carry headers
# NOTE: allow_credentials=True requires specific origins (cannot use "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Local dev
        "http://194.47.170.217",      # Staging
        "http://localhost:3000",      # Alternative dev port
    ],
    allow_credentials=True,           # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_http_client() -> httpx.AsyncClient:
    """Get the HTTP client from app state."""
    return app.state.http_client


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint - no auth required."""
    return HealthResponse()


async def proxy_request(
    request: Request,
    target_url: str,
    token_payload: TokenPayload | None = None,
) -> Response:
    """
    Proxy request to backend service.

    Args:
        request: Original incoming request
        target_url: Backend service URL to forward to
        token_payload: Decoded JWT payload (if authenticated)

    Returns:
        Response from backend service
    """
    # Build headers, forwarding most original headers
    dev_bypass = settings.disable_auth_for_data  # dev toggle: bypass JWT on data routes
    original_x_customer_id = request.headers.get("x-customer-id")  # preserve customer id if provided
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header

    # Strip X-User-* headers that clients might try to inject
    # These headers are trusted internally - only gateway should set them
    for header in ["x-user-id", "x-user-role"]:  # strip user context headers from client
        headers.pop(header, None)
    # Only strip customer header when not in dev bypass (so we can forward it)
    if not dev_bypass:  # only strip customer header when not bypassing
        headers.pop("x-customer-id", None)

    # Add user context headers if authenticated
    if token_payload:
        headers["X-User-ID"] = token_payload.sub
        if token_payload.role:
            headers["X-User-Role"] = token_payload.role
        if token_payload.customer_id:
            headers["X-Customer-ID"] = token_payload.customer_id
    elif dev_bypass:
        # Dev bypass: forward provided X-Customer-ID or use configured default
        if original_x_customer_id:
            headers["X-Customer-ID"] = original_x_customer_id
        elif settings.dev_customer_id:
            headers["X-Customer-ID"] = settings.dev_customer_id

    # Read request body
    body = await request.body()

    try:
        response = await get_http_client().request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )

        # Note: CORS headers are handled by CORSMiddleware globally
        response_headers = dict(response.headers)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )

    except httpx.RequestError as e:
        logger.error("Failed to proxy request to %s: %s", target_url, e)
        raise HTTPException(status_code=502, detail="Backend service unavailable") from e


# Auth routes - NO JWT validation (login/register need to work without token)
@app.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def auth_proxy(request: Request, path: str):
    """Proxy requests to Auth Service without JWT validation."""
    target_url = f"{settings.auth_service_url}/auth/{path}"
    logger.debug("Proxying auth request to: %s", target_url)
    return await proxy_request(request, target_url)


# Ingestion route - JWT validation required, restricted to device/admin/internal roles
INGEST_ALLOWED_ROLES = {"device", "admin", "internal"}


@app.api_route(
    "/api/ingest",
    methods=["POST"],
)
async def ingest_proxy(request: Request):
    """Proxy requests to Ingestion Service with JWT validation and role check."""
    token_payload = await validate_jwt(request)

    # Role-based access control - only device, admin, internal can ingest
    if token_payload.role not in INGEST_ALLOWED_ROLES:
        logger.warning(
            "Ingest rejected for user %s with role %s",
            token_payload.sub,
            token_payload.role,
        )
        raise HTTPException(
            status_code=403,
            detail="Ingestion requires device, admin, or internal role",
        )

    target_url = f"{settings.ingestion_service_url}/ingest"
    logger.debug("Proxying ingest request to: %s (user: %s)", target_url, token_payload.sub)
    return await proxy_request(request, target_url, token_payload)


# Grafana routes - JWT validation required, forwards X-User-* headers
@app.api_route(
    "/api/grafana/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def grafana_proxy(request: Request, path: str):
    """Proxy requests to Grafana with JWT validation and X-User headers."""
    token_payload = await validate_jwt(request)

    # Restrict to internal/admin only (commented out for testing)
    # if token_payload.role not in ["admin", "internal"]:
    #     raise HTTPException(status_code=403, detail="Grafana access requires internal or admin role")

    # Grafana runs with GF_SERVER_SERVE_FROM_SUB_PATH=true, so it expects /api/grafana/ prefix
    target_url = f"{settings.grafana_service_url}/api/grafana/{path}"
    logger.debug("Proxying grafana request to: %s (user: %s)", target_url, token_payload.sub)
    return await proxy_request(request, target_url, token_payload)


# Root grafana endpoint (for /api/grafana without trailing path)
@app.api_route(
    "/api/grafana",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def grafana_proxy_root(request: Request):
    """Proxy requests to Grafana root with JWT validation."""
    token_payload = await validate_jwt(request)

    # Restrict to internal/admin only (commented out for testing)
    # if token_payload.role not in ["admin", "internal"]:
    #     raise HTTPException(status_code=403, detail="Grafana access requires internal or admin role")

    # Grafana runs with GF_SERVER_SERVE_FROM_SUB_PATH=true, so it expects /api/grafana/ prefix
    target_url = f"{settings.grafana_service_url}/api/grafana/"
    logger.debug("Proxying grafana request to: %s (user: %s)", target_url, token_payload.sub)
    return await proxy_request(request, target_url, token_payload)


# ==== ANALYTICS INTEGRATION: Query service routes ====
# Data/Queries routes - JWT validation required, CORS support
@app.api_route(
    "/api/data/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def data_proxy(request: Request, path: str):
    """Proxy requests to Queries Service with JWT validation."""
    # Note: CORS preflight (OPTIONS) is handled by CORSMiddleware

    # Conditionally bypass JWT for local testing
    token_payload = None if settings.disable_auth_for_data else await validate_jwt(request)
    target_url = f"{settings.queries_service_url}/api/data/{path}"
    user_label = token_payload.sub if token_payload else "dev-bypass"
    logger.debug("Proxying data request to: %s (user: %s)", target_url, user_label)
    return await proxy_request(request, target_url, token_payload)


# Root data endpoint (for /api/data without trailing path)
@app.api_route(
    "/api/data",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def data_proxy_root(request: Request):
    """Proxy requests to Queries Service root with JWT validation."""
    # Note: CORS preflight (OPTIONS) is handled by CORSMiddleware

    # Conditionally bypass JWT for local testing
    token_payload = None if settings.disable_auth_for_data else await validate_jwt(request)
    target_url = f"{settings.queries_service_url}/api/data"
    user_label = token_payload.sub if token_payload else "dev-bypass"
    logger.debug("Proxying data request to: %s (user: %s)", target_url, user_label)
    return await proxy_request(request, target_url, token_payload)
# ==== END ANALYTICS INTEGRATION ====
