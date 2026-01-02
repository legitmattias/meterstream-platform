// Environment configuration
export const config = {
  // API base URL - should include the `/api` prefix so frontend calls like
  // `/auth/me` become `http://localhost:8000/api/auth/me` when concatenated.
  // In production set `VITE_API_BASE_URL` to your gateway URL (e.g. "https://your-gateway.example.com/api").
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  grafanaUrl: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000',
  grafanaDashboardUid: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || '',
}
