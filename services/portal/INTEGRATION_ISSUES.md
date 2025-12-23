# Integration & Troubleshooting Notes

This document lists potential problems, their causes, and recommended fixes when running the Portal, Gateway and Queries services together. It is intended as a quick reference for developers running the system locally or diagnosing issues in staging.

**Integration Mapping**
- **Portal**: uses `services/portal/src/lib/api.js` which concatenates `config.apiBaseUrl + endpoint` for all requests. Many calls are made to endpoints such as `/auth/me` and `/data/*`.
- **Gateway**: exposes `/api/auth/*`, `/api/data/*`, `/api/grafana/*`, `/api/ingest` and proxies them to backend services; it injects `X-User-*` and `X-Customer-ID` headers based on JWT validation (or forwards `X-Customer-ID` in dev-bypass mode).
- **Queries**: provides analytics routes under `/api/data/*` and expects `X-Customer-ID` header for customer-isolated endpoints.

**Potential Problems & Symptoms**
- **Missing `/api` in Portal base URL**: Portal concatenates `config.apiBaseUrl + endpoint`. If `config.apiBaseUrl` does not include `/api`, requests like `http://localhost:8000/data/...` will not hit the Gateway proxy (which expects `/api/data/...`) and result in 404s.
  - Symptom: 404s for `/data/*` or `/auth/*` calls in browser network tab.
  - Fix: Ensure `VITE_API_BASE_URL` or the default `services/portal/src/config.js` includes `/api` (e.g. `http://localhost:8000/api`).

- **Inconsistent manual fetch in `Register.jsx`**: `Register.jsx` uses a direct `fetch` with a different default URL (`http://localhost:8080`) instead of using the centralized `api` client.
  - Symptom: Register may call the wrong host/port or omit `/api`, leading to failed registrations in dev.
  - Fix: Replace the manual fetch with `api.register(email, password, name)` or reference `config.apiBaseUrl` consistently.

- **Queries endpoints require `X-Customer-ID`**: Several data endpoints in `services/queries/src/main.py` raise 403 if `X-Customer-ID` is missing. The Gateway sets `X-Customer-ID` from the JWT payload when present; however admin/internal tokens may not include a `customer_id` claim.
  - Symptom: Admin or internal users get 403 responses for `/api/data/*` calls (top-consumers, logs, dashboard) even though the UI is rendering `AdminDashboard`.
  - Fix Options:
    - (Recommended) Adjust Queries endpoint logic: allow admin/internal users to access specific system-level endpoints without `X-Customer-ID` (detect role from `X-User-Role` header). Or expose separate admin endpoints that return global results.
    - Or ensure admin/internal JWTs include a `customer_id` when appropriate.
    - Or have Gateway include a special header for admin/system requests that Queries can trust.

- **Dev auth bypass security (Gateway)**: Gateway supports `disable_auth_for_data` which forwards or sets `X-Customer-ID` for dev convenience. This is dangerous if accidentally enabled in non-dev environments.
  - Symptom: Tests pass in dev but fail in staging/production when bypass is off.
  - Fix: Limit this option to local dev with clear env var names and documentation.

- **CORS / credentials**: The Portal uses cookies for sessions (`credentials: 'include'`). Gateway and backend services must allow credentials and set correct `Access-Control-Allow-Origin` and `allow_credentials` in CORS.
  - Symptom: 401/403 or missing cookie on cross-origin calls.
  - Fix: Ensure `allow_credentials=True` on Gateway/Queries CORS and configure explicit allowed origins (not `*`) when credentials are used.

- **ESLint / npx PowerShell policy**: Running `npx` in PowerShell may be blocked by execution policy (`npx.ps1 cannot be loaded`). Also ESLint v9 expects `eslint.config.*` and may fail if not present.
  - Symptom: Developer cannot run `npx eslint ...` in PowerShell; editor shows lint errors or missing config.
  - Fix: Run lint in Bash, adjust PowerShell execution policy if acceptable, or add an ESLint config compatible with v9.

- **Duplicate or leftover merge artifacts**: During rebases/merges, duplicate route definitions or leftover conflict markers can cause duplicate endpoints or syntax errors.
  - Symptom: FastAPI raises route duplication errors on startup or editor shows conflict markers (`<<<<<<<`).
  - Fix: Remove duplicate route definitions (keep the fully-typed/response-modeled endpoints), remove conflict markers, and ensure no duplicate `@app.get('/path')` definitions remain.

- **Grafana embed and UID**: If `config.grafanaDashboardUid` or `grafanaUrl` are not set correctly, embedded Grafana iframes may show 404 or blank dashboards.
  - Symptom: Blank iframe or 404 inside iframe.
  - Fix: Set `VITE_GRAFANA_URL` and `VITE_GRAFANA_DASHBOARD_UID` correctly for dev/staging, or fallback to a working dashboard URL.

**Quick reproduction / smoke tests**
- Start services: Gateway, Queries, Auth and Portal (Portal can run in dev via `npm run dev`).
- Open browser DevTools → Network. Perform these checks:
  - `GET /api/auth/me` — should return user data when logged in.
  - `GET /api/data/dashboard?...` — should return dashboard JSON. If 403, inspect response body and headers.
  - `GET /api/data/top-consumers` and `GET /api/data/logs` as admin — should return lists (or 403 if Queries requires `X-Customer-ID`).
- If any request returns 404, check the full request URL in Network (missing `/api` or wrong host indicates `apiBaseUrl` mismatch).

**Recommended code fixes / improvements**
- Portal: use centralized `api` client everywhere.
  - Replace manual `fetch` in `services/portal/src/pages/Register.jsx` with `api.register(...)`.
  - Ensure `services/portal/src/config.js` default `apiBaseUrl` includes `/api` during local dev, or require `VITE_API_BASE_URL` to include `/api`.
- Gateway/Queries: make `X-Customer-ID` optional for system-level endpoints, or add separate admin endpoints:
  - Example: have queries check `X-User-Role` header and, if `admin|internal`, allow global aggregation endpoints.
- Gateway: keep `disable_auth_for_data` strictly for dev with clear default `False` and documentation.
- Add small runtime check in Portal dev startup to warn when `config.apiBaseUrl` does not contain `/api`.
- Add minimal CSS classes for `dashboard-error` and `dashboard-loading-data` if desired so messages are visible.

**Environment variables of interest**
- `VITE_GRAFANA_URL`, `VITE_GRAFANA_DASHBOARD_UID` (Portal) — configure Grafana embedding.
- Gateway/Queries: `DISABLE_AUTH_FOR_DATA` / `DEV_CUSTOMER_ID` (or similarly named envs) — ensure these are only set in dev.

**Next steps / checklist**
- [ ] Ensure `VITE_API_BASE_URL` is set correctly in local env / `.env` files and CI.
- [ ] Replace the manual fetch in `Register.jsx` with `api.register(...)`.
- [ ] Decide whether Queries should allow admin/global views without `X-Customer-ID` and implement a small role check if needed.
- [ ] Run an end-to-end smoke test (customer, admin, internal) and verify Dashboard, Top Consumers, Logs, and Grafana embeds.

---
Generated on December 23, 2025
