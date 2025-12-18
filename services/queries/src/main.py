"""Query Service - Analytics data queries with customer isolation."""

import logging
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query

from .config import settings
from .influx import (
    get_influx_client,
    query_consumption,
    query_hourly,
    query_monthly_days,
    query_summary,
    query_total_and_average,
    query_weekly_days,
)
from .models import (
    ConsumptionDataPoint,
    ConsumptionResponse,
    DashboardResponse,
    HealthResponse,
    HourlyData,
    MonthlyDayData,
    SummaryResponse,
    WeeklyDayData,
)

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
    year: str | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    date: str | None = Query(None),
):
    """
    Get all dashboard data at once.

    Args:
        x_customer_id: Customer ID (from gateway header)
        year: Optional year filter ("2024", "2025", "All")
        month: Optional month (1-12) for monthly view
        date: Optional date (YYYY-MM-DD) for hourly view

    Returns:
        Combined weekly, monthly, hourly data and summary statistics
    """
    customer_id = get_customer_id(x_customer_id)

    try:
        client = get_influx_client()
        query_api = client.query_api()

        # Query weekly per-day data
        weekly_data = query_weekly_days(query_api, customer_id, year)
        weekly_days = [WeeklyDayData(day=d["day"], consumption=d["consumption"]) for d in weekly_data]

        # Query monthly per-day data if month provided
        monthly_days = []
        if month and year and year != "All":
            monthly_data = query_monthly_days(query_api, customer_id, int(year), month)
            monthly_days = [MonthlyDayData(day=d["day"], consumption=d["consumption"]) for d in monthly_data]

        # Query hourly data if date provided
        hourly = []
        if date:
            hourly_data = query_hourly(query_api, customer_id, date)
            hourly = [HourlyData(hour=h["hour"], consumption=h["consumption"]) for h in hourly_data]

        # Query total and average
        stats = query_total_and_average(query_api, customer_id, year)

        return DashboardResponse(
            customer_id=customer_id,
            year=year,
            month=month,
            date=date,
            weekly_days=weekly_days,
            monthly_days=monthly_days,
            hourly=hourly,
            total=stats["total"],
            average=stats["average"],
        )

    except Exception as e:
        logger.error("Failed to query dashboard for %s: %s", customer_id, e)
        raise HTTPException(status_code=500, detail="Failed to query data") from e
