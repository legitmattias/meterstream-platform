# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# Root Files
package.json - Lists dependencies (React, react-router-dom) and scripts (npm run dev, npm run build)

vite.config.js - Vite configuration (tells Vite to use React plugin)

Dockerfile - Multi-stage build: 1) Build React app with Node, 2) Serve static files with Nginx

nginx.conf - Nginx config: serves files from /usr/share/nginx/html, enables SPA routing (all routes → index.html), adds /health endpoint

.env.example - Template for environment variables (API URL, Grafana URL). Copy to .env locally

.dockerignore - Tells Docker to skip node_modules, .git when building (faster builds)

index.html - Entry HTML file; Vite injects your React app into <div id="root">

## NGINX
Serves React static files
SPA routing fallback
Health check for K3s

# Architecture:

React app (built with Vite) runs in the browser
Calls gateway service at /api/auth/login to authenticate
Gateway proxies to auth service (http://auth:8000)
Auth service returns JWT token
Portal stores JWT in sessionStorage
All subsequent requests include Authorization: Bearer <token>
Protected routes redirect to login if not authenticated
Dashboard embeds Grafana iframe

## Application Code
main.jsx - Entry point: mounts React app to DOM (<App /> → #root)

App.jsx - Root component: sets up react-router with routes (/login, /dashboard, /)

App.css - Global styles (reset, fonts)

config.js
Reads environment variables (VITE_API_BASE_URL, VITE_GRAFANA_URL) and exports them for use in the app

## api.js - API Client
Class that handles all HTTP requests to backend:

Stores JWT token
Adds Authorization: Bearer <token> header to requests
Handles 401 (unauthorized) → redirects to login
Methods: login(), register(), health()

## src/hooks/useAuth.js - Auth Hook
React hook that manages authentication state:

On mount: checks sessionStorage for access_token, restores session
login(): calls API, stores token, sets user state
logout(): clears token, clears user state
isAuthenticated(): returns true if user logged in
Returns: { user, loading, login, logout, isAuthenticated }

## src/components/ProtectedRoute.jsx
Wrapper component that protects routes:

Checks if user is authenticated
If yes → shows child component (Dashboard)
If no → redirects to /login

## src/pages/Login.jsx + Login.css
Login form:

Input: email, password
On submit → calls useAuth().login() → navigates to /dashboard on success
Shows error message if login fails

## src/pages/Dashboard.jsx + Dashboard.css
Protected dashboard page:

Shows header with user email + logout button
Status cards (placeholder)
Grafana iframe embed (shows dashboards from VITE_GRAFANA_URL)
Link to open Grafana in new tab

# portal - Kubernetes Manifests
deployment.yaml - Defines portal pods (2 replicas, Nginx container, health checks, resource limits)

service.yaml - Exposes portal internally (ClusterIP on port 80)

README.md - Docs for deploying portal to K8s

# API contracts match:

Portal calls /api/auth/login with {email, password} → Gateway routes to auth service
Auth service expects email and password (lines 43-51 in auth_router.py)
Auth returns {access_token, refresh_token, ...} → Portal stores access_token

# JWT handling:

Portal stores JWT in sessionStorage via useAuth hook
Adds Authorization: Bearer <token> to all requests (api.js line 29)
Gateway validates JWT and extracts claims (main.py lines 78-86)
Gateway adds X-User-ID, X-User-Role, X-Customer-ID headers (lines 87-92)

# Error handling:

Portal redirects to /login on 401 (api.js line 42)
Auth service returns proper HTTP status codes

# Architecture:
User browser 
  → Traefik (reverse proxy, port 443) 
    → Portal service (K3s) 
      → Nginx container (serves React files, port 80)

Portal → Gateway (/api/auth/*) → Auth Service (FastAPI)
Follows the same pattern as other services (ingestion, processor)
Gateway acts as single entry point with JWT validation

## Recent updates (2025-12-22)

  - `GET /api/data/dashboard` — weekly, monthly, hourly series plus `total` and `average`.
  - `GET /api/data/quality` — returns simple quality metrics (completeness implemented; accuracy/timeliness placeholders).
  - `GET /api/data/top-consumers` — returns top customers aggregated from Influx (groups by `consumer.id` tag).
  - `GET /api/data/logs` — currently a placeholder returning an empty array (no centralized log store implemented in the repo).

 Influx tag name: `top-consumers` groups by the `consumer.id` tag. If your Influx points use a different tag name (for example `customer_id`), update the Flux query in `services/queries/src/influx.py` accordingly.

- X-Customer-ID requirement: The Query Service requires `X-Customer-ID` on `/api/data/*` endpoints to enforce customer isolation. The Gateway must extract and forward this from a validated JWT (or run in dev-bypass mode with `DEV_CUSTOMER_ID`). Without it, requests will return 403.
- Quality metrics: `accuracy` and `timeliness` are not implemented (placeholders). Decide on the definitions and data sources for these metrics so they can be implemented correctly.
- Logs: `GET /api/data/logs` is a placeholder. If you want real logs in the admin UI, add or point to a log store (Loki, Elasticsearch, or a logs endpoint).
- Register consistency: Some local edits may have reverted portal changes — `Register.jsx` should use the shared API client (`api.register`) for consistency; if you prefer that I can re-apply it.
- Accessibility: Chart bars use `div` with `role="button"` but are missing keyboard handlers; consider adding `onKeyDown` to support keyboard activation.

# TODO 
## Making Logs Dynamic
1. Create a logs endpoint in a backend service (e.g., gateway or new logs service)

Add route: GET /api/logs that returns recent logs from your system
Query logs from NATS, InfluxDB, or a centralized logging service
Return JSON: [{level: "INFO", message: "...", timestamp: "..."}]

2. Add a logs API call in api.js

Create method: async getLogs() { return this.request('/api/logs'); }
Use the existing request method with auth headers

## Top Consumers Table:

Create endpoint: GET /api/analytics/top-consumers returning [{id, name, consumption, change}]
Fetch in Dashboard with useEffect and store in useState
Map over real data instead of hardcoded rows
Sort by consumption descending, take top 5

# Data Quality Metrics:

Create endpoint: GET /api/analytics/data-quality returning {completeness, accuracy, timeliness} as percentages
Fetch and store in state
Update progress bar widths dynamically with style={{width: ${quality.completeness}%}}
Calculate from actual data ingestion stats (missing records, validation errors, delayed messages)

# Summary Cards:

Create endpoint: GET /api/analytics/summary returning {totalConsumption, costEstimate, averageDaily}
Fetch and display real values
Pull from InfluxDB aggregations (sum, average queries)

# ADMIN DASHBOARD
- system overview (GRAFANA)

# INTERNAL DASHBOARD
- Consumer Analytics (GRAFANA)

# LANDING PAGE
- Same for all
- link to grafana for internal och admin

# USER SETTINGS PAGE (optional)

# MINA SIDOR DASHBOARD
- Individual data consumption

# Recommended next work 

Implement Influx-backed top-consumers aggregate (group by consumer.id) in influx.py and wire it into /api/data/top-consumers 

Implement a simple completeness metric for data-quality (e.g., presence of expected daily points over last 7 days) and add accuracy/timeliness definitions.

Wire logs to a log store (Loki/Elasticsearch) or a small log table if you have logs centrally.