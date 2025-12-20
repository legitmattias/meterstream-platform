# ==============================================================================
# ANALYTICS INTEGRATION: Queries Service README
# ==============================================================================
# This service was added as part of the analytics integration to provide
# time-series data queries from InfluxDB with customer isolation.
#
# Endpoints:
# - GET /api/data/dashboard - Dashboard summary with weekly/monthly/hourly data
# - GET /api/data/consumption - Consumption data (daily/weekly/monthly)
# - GET /api/data/summary - Summary statistics
#
# Dependencies:
# - InfluxDB (for time-series data storage)
# - Gateway (proxies requests with JWT validation and customer context)
# ==============================================================================
