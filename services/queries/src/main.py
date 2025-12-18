"""Query Service - Analytics data queries with customer isolation."""

import logging
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query

from .config import settings
from .influx import get_influx_client, query_consumption, query_summary
from .models import ConsumptionDataPoint, ConsumptionResponse, DashboardResponse, HealthResponse, SummaryResponse

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Query Service",
    description="Analytics queries with customer isolation",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse()


def get_customer_id(x_customer_id: Annotated[str | None, Header()] = None) -> str:
    """Extract and validate customer ID from headers."""
    if not x_customer_id:
        raise HTTPException(status_code=403, detail="X-Customer-ID header required")
    return x_customer_id


@app.get("/api/data/consumption", response_model=ConsumptionResponse)
async def get_consumption(
    x_customer_id: Annotated[str, Header()] = None,
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
):
    """
    Get consumption data for authenticated customer.

    Args:
        x_customer_id: Customer ID (from gateway header)
        period: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months)

    Returns:
        Consumption data points with timestamps
    """
    customer_id = get_customer_id(x_customer_id)

    try:
        client = get_influx_client()
        query_api = client.query_api()

        data = query_consumption(query_api, customer_id, period)

        return ConsumptionResponse(
            customer_id=customer_id,
            period=period,
            data=[
                ConsumptionDataPoint(timestamp=d["timestamp"], consumption=d["consumption"])
                for d in data
            ],
        )

    except Exception as e:
        logger.error("Failed to query consumption for %s: %s", customer_id, e)
        raise HTTPException(status_code=500, detail="Failed to query data") from e


@app.get("/api/data/summary", response_model=SummaryResponse)
async def get_summary(
    x_customer_id: Annotated[str, Header()] = None,
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
):
    """
    Get consumption summary for authenticated customer.

    Args:
        x_customer_id: Customer ID (from gateway header)
        period: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months)

    Returns:
        Summary statistics (total and average)
    """
    customer_id = get_customer_id(x_customer_id)

    try:
        client = get_influx_client()
        query_api = client.query_api()

        stats = query_summary(query_api, customer_id, period)

        return SummaryResponse(
            customer_id=customer_id,
            period=period,
            **stats,
        )

    except Exception as e:
        logger.error("Failed to query summary for %s: %s", customer_id, e)
        raise HTTPException(status_code=500, detail="Failed to query data") from e


@app.get("/api/data/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    x_customer_id: Annotated[str, Header()] = None,
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
):
    """
    Get all dashboard data at once (consumption + summary).

    Args:
        x_customer_id: Customer ID (from gateway header)
        period: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months)

    Returns:
        Combined consumption data and summary statistics
    """
    customer_id = get_customer_id(x_customer_id)

    try:
        client = get_influx_client()
        query_api = client.query_api()

        # Query both at once
        consumption_data = query_consumption(query_api, customer_id, period)
        summary_stats = query_summary(query_api, customer_id, period)

        consumption_points = [
            ConsumptionDataPoint(timestamp=d["timestamp"], consumption=d["consumption"])
            for d in consumption_data
        ]

        summary = SummaryResponse(
            customer_id=customer_id,
            period=period,
            **summary_stats,
        )

        return DashboardResponse(
            customer_id=customer_id,
            period=period,
            consumption=consumption_points,
            summary=summary,
        )

    except Exception as e:
        logger.error("Failed to query dashboard for %s: %s", customer_id, e)
        raise HTTPException(status_code=500, detail="Failed to query data") from e
