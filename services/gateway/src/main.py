"""API Gateway - JWT validation and request proxying to backend services."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
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
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header

    # Strip X-User-* headers that clients might try to inject
    # These headers are trusted internally - only gateway should set them
    for header in ["x-user-id", "x-user-role", "x-customer-id"]:
        headers.pop(header, None)

    # Add user context headers if authenticated
    if token_payload:
        headers["X-User-ID"] = token_payload.sub
        if token_payload.role:
            headers["X-User-Role"] = token_payload.role
        if token_payload.customer_id:
            headers["X-Customer-ID"] = token_payload.customer_id

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

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
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


# Ingestion route - JWT validation required
@app.api_route(
    "/api/ingest",
    methods=["POST"],
)
async def ingest_proxy(request: Request):
    """Proxy requests to Ingestion Service with JWT validation."""
    token_payload = await validate_jwt(request)
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
    target_url = f"{settings.grafana_service_url}/{path}"
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
    target_url = settings.grafana_service_url
    logger.debug("Proxying grafana request to: %s (user: %s)", target_url, token_payload.sub)
    return await proxy_request(request, target_url, token_payload)
