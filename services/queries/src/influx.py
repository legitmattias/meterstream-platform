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


def query_weekly_days(
    query_api: QueryApi,
    customer_id: str,
    year: str | None = None,
) -> list[dict[str, Any]]:
    """
    Query last 7 days of consumption grouped by day of week.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        year: Optional year filter ("2024", "2025", or None for all)

    Returns:
        List of {day: "Mon", consumption: float} dicts
    """
    year_filter = ""
    if year and year != "All":
        year_filter = f'|> filter(fn: (r) => r._time >= {year}-01-01T00:00:00Z and r._time < {int(year)+1}-01-01T00:00:00Z)'

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: -7d)
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
    |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
      {year_filter}
      |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
      |> sort(columns: ["_time"])
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    day_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    results = {day: 0.0 for day in day_map.values()}

    for table in tables:
        for record in table.records:
            timestamp = record.get_time()
            day_index = timestamp.weekday()
            day_name = day_map[day_index]
            results[day_name] += float(record.get_value() or 0)

    return [{"day": day, "consumption": results[day]} for day in day_map.values()]


def query_monthly_days(
    query_api: QueryApi,
    customer_id: str,
    year: int,
    month: int,
) -> list[dict[str, Any]]:
    """
    Query daily consumption for a specific month.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        year: Year (2024, 2025, etc.)
        month: Month (1-12)

    Returns:
        List of {day: 1-31, consumption: float} dicts
    """
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start_date.isoformat()}Z, stop: {end_date.isoformat()}Z)
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
    |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
      |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
      |> sort(columns: ["_time"])
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    results = {}
    for table in tables:
        for record in table.records:
            timestamp = record.get_time()
            day = timestamp.day
            if day not in results:
                results[day] = 0.0
            results[day] += float(record.get_value() or 0)

    # Return days 1-31 (or however many days in month)
    days_in_month = (end_date - start_date).days
    return [{"day": d, "consumption": results.get(d, 0.0)} for d in range(1, days_in_month + 1)]


def query_hourly(
    query_api: QueryApi,
    customer_id: str,
    date_str: str,
) -> list[dict[str, Any]]:
    """
    Query hourly consumption for a specific date.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        date_str: Date string in YYYY-MM-DD format

    Returns:
        List of {hour: 0-23, consumption: float} dicts
    """
    date = datetime.fromisoformat(date_str)
    start = date.replace(hour=0, minute=0, second=0)
    end = start + timedelta(days=1)

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
    |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
      |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)
      |> sort(columns: ["_time"])
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    results = {h: 0.0 for h in range(24)}
    for table in tables:
        for record in table.records:
            timestamp = record.get_time()
            hour = timestamp.hour
            results[hour] += float(record.get_value() or 0)

    return [{"hour": h, "consumption": results[h]} for h in range(24)]


def query_total_and_average(
    query_api: QueryApi,
    customer_id: str,
    year: str | None = None,
) -> dict[str, float]:
    """
    Query total and average consumption.

    Args:
        query_api: InfluxDB query API instance
        customer_id: Customer ID to filter by
        year: Optional year filter ("2024", "2025", "All", or None)

    Returns:
        Dict with total and average
    """
    year_filter = ""
    if year and year != "All":
        year_filter = f'|> filter(fn: (r) => r._time >= {year}-01-01T00:00:00Z and r._time < {int(year)+1}-01-01T00:00:00Z)'

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: -365d)
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
    |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
      {year_filter}
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    values = []
    for table in tables:
        for record in table.records:
            val = record.get_value()
            if val is not None:
                values.append(float(val))

    if not values:
        return {"total": 0.0, "average": 0.0}

    return {
        "total": sum(values),
        "average": sum(values) / len(values),
    }


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
    |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
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
      |> filter(fn: (r) => r["consumer.id"] == "{customer_id}")
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


def query_top_consumers(
    query_api: QueryApi,
    limit: int = 5,
    days: int = 30,
) -> list[dict[str, Any]]:
    """
    Query top consumers across customers by summed consumption over the last `days`.

    Returns: list of {name: customer_id, consumption: float}
    """
    start = f"-{days}d"

    flux_query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start})
      |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
      |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
    |> group(columns: ["consumer.id"])
      |> sum(column: "_value")
      |> sort(columns: ["_value"], desc: true)
      |> limit(n: {limit})
    '''

    tables = query_api.query(flux_query, org=settings.influx_org)

    results: dict[str, float] = {}
    for table in tables:
        for record in table.records:
            customer = record.values.get("consumer.id") or record.values.get("consumer_id") or "unknown"
            val = record.get_value()
            if val is None:
                continue
            results[customer] = results.get(customer, 0.0) + float(val)

    return [{"name": k, "consumption": v} for k, v in sorted(results.items(), key=lambda kv: kv[1], reverse=True)][:limit]


def query_quality_metrics(
    query_api: QueryApi,
    customer_id: str,
    period: str = "daily",
) -> dict[str, Any]:
    """
    Compute simple data quality metrics based on presence of consumption points.

    - completeness: percent of expected windows that have data (>0)
    - accuracy: not implemented (returns None)
    - timeliness: not implemented (returns None)

    Returns dict with keys completeness, accuracy, timeliness
    """
    # Map period to expected number of points (matches query_consumption windows)
    expected_map = {"daily": 24, "weekly": 4, "monthly": 12}
    expected = expected_map.get(period, 24)

    try:
        data = query_consumption(query_api, customer_id, period)
        observed = sum(1 for d in data if (d.get("consumption") is not None and float(d.get("consumption", 0)) != 0))

        completeness = None
        if expected > 0:
            completeness = (observed / expected) * 100.0

        return {"completeness": round(completeness, 2) if completeness is not None else None, "accuracy": None, "timeliness": None}
    except Exception:
        return {"completeness": None, "accuracy": None, "timeliness": None}
