# AI Context Summary

## TL;DR
- Streamlit underwriting tool with clean separation between UI, services, and pure financial math.
- `src/app.py` is the Streamlit entry point; `run.sh` bootstraps a venv and launches the app.
- Providers (Zillow, Rentometer, ATTOM, ClosingCorp, mock) feed property data into analysis workflows.
- Core calculations are pure, unit-tested helpers—keep them deterministic.

## Mission & Scope
- Help property investors evaluate rental and flip opportunities quickly.
- Maintain modular boundaries so teams can swap providers, extend UI, or add persistence without breaking core logic.

## Runtime Entry Points
- `src/app.py`: Collects assumptions, orchestrates data fetch, and renders results in Streamlit.
- `run.sh`: Convenience launcher (creates virtualenv, installs dependencies, runs Streamlit).

## Architecture Map
| Layer | Path | Responsibilities |
| --- | --- | --- |
| UI | `src/ui/ui_components.py` | Streamlit widgets converting user input into dataclasses. |
| Services | `src/services/analysis_service.py` | Runs rental and flip analyses via `core.calculations`. |
| Services | `src/services/data_fetch.py` + `providers/` | Calls configured providers, merges payloads into `PropertyData`. |
| Core | `src/core/models.py` | Dataclasses for property assumptions, results, and provenance (`ApiSource`). |
| Core | `src/core/calculations.py` | Pure math helpers (NOI, cap rate, IRR, mortgage, etc.). |
| Utilities | `src/utils/config.py`, `logging.py`, `currency.py` | Settings, logging, USD formatting. |

## Key Workflows
1. User submits address and assumptions in Streamlit.
2. `data_fetch.fetch_property` queries providers (mock by default) and merges results.
3. `analysis_service` runs rental or flip scenarios using pure core helpers.
4. UI renders values with currency formatting.

## Configuration Notes
- Copy `.env.example` to `.env`; populate provider keys and base URLs.
- Important settings: `ZILLOW_API_KEY`, `RENTOMETER_API_KEY`, `ATTOM_API_KEY`, `CLOSINGCORP_API_KEY`, `PROVIDER_TIMEOUT_SEC`, `USE_MOCK_PROVIDER_IF_NO_KEYS`.
- Settings govern provider timeouts, mock fallbacks, and optional defaults (e.g., Rentometer bedroom count).

## Delivery Status
- **Provider wiring**: Zillow, Rentometer, ATTOM, ClosingCorp, and mock clients implemented with structured logging and tests.
- **Data merge**: `data_fetch.merge` keeps provenance and combines payloads safely.
- **UI alignment**: Streamlit forms map to dataclasses and normalize user-friendly inputs (percentages to decimals).
- **Analysis validation**: Rental/flip flows use configurable assumptions; IRR and carrying costs verified by tests.
- **Testing**: 21 pytest cases cover calculations, services, provider clients, and merge logic.

## Outstanding Work
- ClosingCorp provider still needs a real production endpoint; returns `None` when unconfigured.
- Streamlit output is a basic key/value list—consider richer visuals and unit-aware formatting.
- Caching/persistence layer not implemented yet (settings exist for TTL).

## Next Suggested Steps
1. Add real API credentials and smoke-test each provider against production services.
2. Introduce caching and rate-limit handling once usage patterns are known.
3. Upgrade Streamlit results (charts, tables, export options).
4. Layer in persistence (database) and authentication per roadmap priorities.

Keep this file aligned with architectural or workflow changes so new contributors can ramp quickly.
