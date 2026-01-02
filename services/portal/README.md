# Portal :  React + Vite

This README describes the Portal (frontend) for MeterStream: a React/Vite app that provides the customer-facing dashboard and admin links. It documents purpose, configuration, development workflow, API contracts, and verification steps.

## Purpose

The Portal is the web UI customers use to view their electricity consumption analytics and the admin/internal users use to open Grafana operational dashboards. The Portal authenticates users, requests analytics from the Gateway/Queries services, and renders charts and summary cards. By default customers see the most recent available year (server-resolved "latest") and can select other available years from a server-populated dropdown.

## Quick links
- Dashboard code: `services/portal/src/pages/Dashboard.jsx`
- Auth handling: `services/portal/src/contexts/AuthContext.jsx`
- API client: `services/portal/src/lib/api.js`

## Environment variables
Copy `.env.example` to `.env` (or set env vars in your dev environment). Important variables:

- `VITE_API_BASE_URL` — base URL for backend Gateway (e.g. `http://localhost:8000`). The client prefixes paths with this value when calling `/auth`, `/data` and other API endpoints.
- `VITE_GRAFANA_URL` — Grafana base URL used for iframe/embed links.

## Run locally (development)

1. Install dependencies and start dev server:

```bash
cd services/portal
npm install
npm run dev
```

2. Open the app in the browser (Vite prints the local URL, typically `http://localhost:5173`).

Notes:
- The Portal uses cookies and/or HttpOnly cookies for auth flows. During local development you may need the Gateway and Auth services running (or a dev auth bypass) to log in.
- Ensure `VITE_API_BASE_URL` points to your Gateway; the Gateway is responsible for validating tokens and forwarding `X-Customer-ID` and `X-User-Role` headers to the Queries service.

## Build and Docker

The `Dockerfile` implements a multi-stage build: build the React app with Node and serve static files with Nginx. To build locally:

```bash
cd services/portal
docker build -t meterstream-portal:local .
```

Run the image:

```bash
docker run --rm -p 8080:80 -e VITE_API_BASE_URL="http://gateway:8000" meterstream-portal:local
```

## Kubernetes

Manifests are in `services/portal/k8s` (deployment, service). Ensure the `VITE_API_BASE_URL` env var is set via a ConfigMap or injected at build time.

## Authentication & API contract

- Login endpoint: POST `${VITE_API_BASE_URL}/auth/login` with `{ email, password }` — Gateway proxies to Auth service and sets auth cookies or returns tokens per project setup.
- The Portal uses the API client (`src/lib/api.js`) which attaches cookies and handles 401 refresh flows. The Gateway must forward identity headers to internal services for tenant isolation.
- Important: The Queries endpoints under `/data` require `X-Customer-ID` for customer-scoped queries. The Gateway extracts this value from the validated JWT and forwards it. Admin/internal roles can omit `X-Customer-ID` for global views.

## Dashboard behavior (important UX rules)

- Default: `selectedYear === 'latest'` — the frontend omits a `year` param when asking for dashboard data. The backend resolves the latest available year for the customer and returns data for it.
- Available years: backend returns `available_years` in the `/api/data/dashboard` response; the dropdown is populated from this list so customers only see years they have data for.
- Selecting a year: when the user selects a specific year the frontend sends `?year=YYYY` and the backend respects explicit years. Charts and the summary cards update to reflect the selected year.
- Summary cards: frontend displays `data.total` and `data.average` from the API when provided; otherwise it falls back to client-side computed values.

## Grafana (admins/internal)

Grafana is used for ops/internal dashboards and reads directly from InfluxDB. The Portal may embed Grafana iframes for admin users, but customers should use the Portal + Queries API for user-facing analytics.

## Testing

- Unit tests (frontend) — run with your project's frontend test runner if available. The repository includes pytest tests for backend services under `services/*/tests`.

## Troubleshooting

- 403 from `/api/data/*`: Gateway did not forward `X-Customer-ID` or the token did not contain a customer claim. Check Gateway logs and JWT contents.
- 401 on requests: session expired or refresh token missing — the API client attempts refresh; if refresh fails you will be redirected to `/login`.
- Charts not showing data: verify Queries service is reachable and InfluxDB contains data for the requested year.

## Where to look in the repo

- Dashboard: `services/portal/src/pages/Dashboard.jsx`
- API client: `services/portal/src/lib/api.js`
- Auth context: `services/portal/src/contexts/AuthContext.jsx`
- Components: `services/portal/src/components/*`

