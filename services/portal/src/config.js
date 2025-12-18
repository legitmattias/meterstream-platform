// Environment configuration
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080', 
  grafanaUrl: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000', 
  grafanaDashboardUid: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || '',
}
