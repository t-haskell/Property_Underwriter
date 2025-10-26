# AI Context Summary

## TL;DR
- FastAPI backend with shared services powering both a Next.js frontend and a legacy Streamlit UI.
- `src/api/main.py` boots the REST API; `run_api.sh` provisions a venv, installs deps, and starts Uvicorn.
- Providers (RentCast, Estated, Redfin, Zillow, Rentometer, ATTOM, ClosingCorp, mock) feed property data into the underwriting workflows.
- Core calculations stay deterministic in `src/core` and are exercised by backend tests and the new web client.

## Mission & Scope
- Enable investors to underwrite rental and flip deals quickly with provider-backed data and persistent history.
- Keep service boundaries clean so additional providers, UI channels, or storage options can be added without touching core math.

## Runtime Entry Points
- `src/api/main.py`: FastAPI router exposing health, address lookup, property fetch, and analysis endpoints.
- `frontend/app/page.tsx`: Next.js client that consumes the API and visualizes merged property payloads.
- `src/app.py`: Streamlit fallback that reuses the same services for rapid validation.
- `run_api.sh` / `run.sh`: Convenience scripts for spinning up the API or Streamlit flows.

## Architecture Map
| Layer | Path | Responsibilities |
| --- | --- | --- |
| Frontend | `frontend/app/`, `frontend/components/` | Address autocomplete, assumption forms, result visualizations powered by the API. |
| API | `src/api/main.py`, `src/api/schemas.py` | FastAPI app, request/response validation, dependency wiring. |
| Services | `src/services/analysis_service.py` | Rental & flip orchestration leveraging core calculations. |
| Services | `src/services/data_fetch.py` + `providers/` | Calls configured providers, merges payloads, persists snapshots. |
| Services | `src/services/nominatim_places.py` | Address suggestion/normalization via Nominatim. |
| Services | `src/services/persistence.py` | SQLite-backed repository for properties and analysis history. |
| Core | `src/core/models.py`, `src/core/calculations.py` | Typed domain models and deterministic financial math. |
| Utilities | `src/utils/config.py`, `src/utils/logging.py` | Settings (Pydantic), logging helpers, currency formatting. |

## Key Workflows
1. User selects an address via Nominatim suggestions or manual entry in the Next.js client.
2. Frontend POSTs to `/api/property/fetch`; backend aggregates providers, caches results, and returns a merged `PropertyData` payload.
3. User submits rental or flip assumptions; `/api/analyze/*` routes compute outcomes using `analysis_service` and core calculations.
4. Results and assumptions persist in SQLite for auditability and future comparisons.

## Configuration Notes
- Copy `.env.example` to `.env`; populate provider API keys, timeouts, and `DATABASE_URL` as needed.
- Frontend can override the backend host via `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`.
- Settings dictate whether the mock provider is used when real credentials are missing and how long cached snapshots live.

## Delivery Status
- **Provider aggregation**: RentCast, Estated, Redfin, Zillow, Rentometer, ATTOM, ClosingCorp wired with logging and graceful fallbacks.
- **Address services**: Nominatim suggest/resolve endpoints power the frontend autocomplete experience.
- **Persistence**: SQLite repository stores merged property data, provider provenance, and analysis runs with timestamps.
- **Frontend**: Next.js UI supports rental/flip flows, raw payload inspection, and assumption defaults mirroring backend models.
- **Testing**: Pytest suite validates calculations, services, persistence; frontend has Vitest/Storybook tooling available.

## Outstanding Work
- Harden provider error handling and introduce rate limiting/caching for production credentials.
- Expand frontend visualizations (charts, sensitivity analyses) and export options.
- Add authentication/authorization when multi-tenant access becomes necessary.

## Next Suggested Steps
1. Smoke-test each provider with real credentials and record usage quotas.
2. Integrate frontend lint/test commands into CI alongside backend checks.
3. Enhance analytics output (e.g., charts, breakdown tables) to leverage stored historical analyses.
4. Plan for background jobs or queues if provider latency increases with higher load.

Keep this file aligned with architectural or workflow changes so new contributors can ramp quickly.

