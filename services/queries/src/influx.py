"""InfluxDB query helpers."""

from datetime import datetime, timedelta
from typing import Any

from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi

from .config import settings


def get_influx_client() -> InfluxDBClient:
    """Get InfluxDB client."""
    return InfluxDBClient(
        url=settings.influx_url,
        token=settings.influx_token,
        org=settings.influx_org,
    )


def query_consumption(
    query_api: QueryApi,
    customer_id: str,
    period: str = "daily",
) -> list[dict[str, Any]]:
    """
    Query consumption data for a customer.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        period: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months)

    Returns:
        List of {timestamp, consumption} dicts
    """
    period_config = {
        "daily": {"range": "-24d", "window": "1d"},
        "weekly": {"range": "-4w", "window": "1w"},
        "monthly": {"range": "-12mo", "window": "30d"},
    }

    if period not in period_config:
        period = "daily"

    config = period_config[period]
    start = config["range"]
    window = config["window"]

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start})
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
      |> filter(fn: (r) => r.customer == "{customer_id}")
      |> aggregateWindow(every: {window}, fn: sum, createEmpty: false)
      |> sort(columns: ["_time"])
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    results = []
    for table in tables:
        for record in table.records:
            results.append({
                "timestamp": record.get_time().isoformat(),
                "consumption": record.get_value(),
            })

    return results


def query_summary(
    query_api: QueryApi,
    customer_id: str,
    period: str = "daily",
) -> dict[str, float]:
    """
    Query summary stats for a customer.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        period: "daily" (24 days), "weekly" (4 weeks), or "monthly" (12 months)

    Returns:
        Dict with total and average consumption
    """
    period_config = {
        "daily": "-24d",
        "weekly": "-4w",
        "monthly": "-12mo",
    }

    if period not in period_config:
        period = "daily"

    start = period_config[period]

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start})
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
      |> filter(fn: (r) => r.customer == "{customer_id}")
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    values = []
    for table in tables:
        for record in table.records:
            val = record.get_value()
            if val is not None:
                values.append(float(val))

    if not values:
        return {
            "total": 0.0,
            "average": 0.0,
        }

    return {
        "total": sum(values),
        "average": sum(values) / len(values),
    }
