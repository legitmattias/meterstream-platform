// Environment configuration
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080', // http://gateway-service:8080 (k3 DNS name)
  grafanaUrl: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000', // http://grafana-service:3000 (k3 DNS name)
  grafanaDashboardUid: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || '',
}
