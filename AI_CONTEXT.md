# AI Context Summary

## Project Mission
- Build a Streamlit application that helps property investors underwrite rental and flip opportunities.
- Provide a clean separation between UI, services, core financial math, and external data providers so the app can be extended safely.

## Runtime Entry Points
- `src/app.py` – Streamlit UI. Collects user inputs, fetches property data, and displays analysis results.
- `run.sh` – Convenience script to create a virtualenv, install requirements, and launch Streamlit.

## Key Packages
```
src/
├─ app.py                 # Streamlit application
├─ core/                  # Domain models + financial calculations
├─ services/              # Analysis orchestration + data providers
├─ ui/                    # Streamlit form components
└─ utils/                 # Configuration, logging, formatting helpers
```

### Core Layer (`src/core`)
- `models.py`: Dataclasses for addresses, property data, rental/flip assumptions, and results. `ApiSource` enum tracks provenance.
- `calculations.py`: Pure math helpers (NOI, cap rate, IRR, mortgage payments, etc.). These functions are unit tested and should remain side-effect free.

### Services Layer (`src/services`)
- `analysis_service.py`: Translates assumptions + property data into results by calling `core.calculations` (rental + flip flows both covered, no hard-coded placeholders).
- `data_fetch.py`: Builds a provider chain, calls each provider, and merges results into a single `PropertyData` object.
- `providers/`: Concrete `PropertyDataProvider` implementations for Zillow, Rentometer, ATTOM, ClosingCorp, and a mock fallback. Each provider includes HTTP integrations with structured logging and graceful degradation.

### UI Layer (`src/ui`)
- `ui_components.py`: Streamlit widgets that collect addresses and analysis assumptions, returning dataclass instances.

### Utilities (`src/utils`)
- `config.py`: Loads environment variables via Pydantic (`Settings`). Controls API keys, base URLs, timeouts, and whether to fall back to the mock provider.
- `logging.py`: Basic logger configuration used throughout the app.
- `currency.py`: Simple USD string formatter.

## Environment & Configuration
- Copy `.env.example` to `.env` and populate keys.
- Important settings:
  - `ZILLOW_API_KEY`: Required for live Zillow/Bridge Interactive data.
  - `RENTOMETER_API_KEY`, `ATTOM_API_KEY`, `CLOSINGCORP_API_KEY`: Enable additional providers when set.
  - Base URLs and optional defaults (e.g. Rentometer bedroom count) are configurable through the same settings file.
  - `PROVIDER_TIMEOUT_SEC`: Shared HTTP timeout for all providers.
  - `USE_MOCK_PROVIDER_IF_NO_KEYS`: Ensures the app still works without live providers.

## Current Data Flow
1. UI captures address and assumptions.
2. `services.data_fetch.fetch_property` calls configured providers (mock by default).
3. `analysis_service` runs rental or flip analysis using core calculations.
4. Streamlit displays the result fields with USD formatting where appropriate.

## Readiness Checklist for Real Data
1. **Provider wiring** ✅
   - Live provider clients implemented for Zillow, Rentometer, ATTOM, and ClosingCorp with request mocking tests.
2. **Data merging** ✅
   - `data_fetch.merge` safely combines payloads, preserving metadata and provenance.
3. **UI alignment** ✅
   - Streamlit forms map directly to dataclass fields and convert user-friendly percentages into decimals where required.
4. **Analysis validation** ✅
   - Rental and flip analyses now use configurable assumptions (no magic constants) and compute IRR/carry costs correctly.
5. **Testing** ✅
   - Expanded pytest suite covers calculations, analysis services, provider clients, and merge logic (21 tests total).

## Known Gaps / TODOs
- ClosingCorp provider requires a real API endpoint for production use; currently expects a generic POST payload and returns `None` if no endpoint is configured.
- Streamlit result rendering is still a plain list of key/value pairs; consider richer visuals and unit-aware formatting.
- No persistence or caching layer is wired up yet (even though settings exist for TTL).

## Suggested Implementation Sequence
1. Integrate real API credentials and smoke-test each provider against the live services.
2. Add response caching/rate-limit handling once provider usage patterns are understood.
3. Enhance the Streamlit results UI (charts, tables, explanatory text) and consider export options.
4. Introduce persistence (database) and authentication per the longer-term roadmap.

Keep this file updated as you make architectural changes so future agents can ramp quickly.