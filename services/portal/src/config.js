// Environment configuration
export const config = {
  // API base URL - includes /api prefix (e.g., "/api" in production, "http://localhost:8000" in dev)
  // Endpoints should NOT include /api prefix - it's added automatically via this base URL
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  grafanaUrl: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000',
  grafanaDashboardUid: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || '',
}
