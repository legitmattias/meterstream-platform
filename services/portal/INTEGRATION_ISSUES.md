# Integration & Troubleshooting Notes

This document lists potential problems, their causes, and recommended fixes when running the Portal, Gateway and Queries services together. It is intended as a quick reference for developers running the system locally or diagnosing issues in staging.

**Integration Mapping**
- **Portal**: uses `services/portal/src/lib/api.js` which concatenates `config.apiBaseUrl + endpoint` for all requests. Many calls are made to endpoints such as `/auth/me` and `/data/*`.
- **Gateway**: exposes `/api/auth/*`, `/api/data/*`, `/api/grafana/*`, `/api/ingest` and proxies them to backend services; it injects `X-User-*` and `X-Customer-ID` headers based on JWT validation (or forwards `X-Customer-ID` in dev-bypass mode).
- **Queries**: provides analytics routes under `/api/data/*` and expects `X-Customer-ID` header for customer-isolated endpoints.


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
- Gateway/Queries: make `X-Customer-ID` optional for system-level endpoints, or add separate admin endpoints:
  - Example: have queries check `X-User-Role` header and, if `admin|internal`, allow global aggregation endpoints.
- Gateway: keep `disable_auth_for_data` strictly for dev with clear default `False` and documentation.
- Add minimal CSS classes for `dashboard-error` and `dashboard-loading-data` if desired so messages are visible.

**Environment variables of interest**
- `VITE_GRAFANA_URL`, `VITE_GRAFANA_DASHBOARD_UID` (Portal) — configure Grafana embedding.
- Gateway/Queries: `DISABLE_AUTH_FOR_DATA` / `DEV_CUSTOMER_ID` (or similarly named envs) — ensure these are only set in dev.

**Next steps / checklist**
- [ ] Decide whether Queries should allow admin/global views without `X-Customer-ID` and implement a small role check if needed.
- [ ] Run an end-to-end smoke test (customer, admin, internal) and verify Dashboard, Top Consumers, Logs, and Grafana embeds.

---
Generated on December 23, 2025

