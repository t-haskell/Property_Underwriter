# Property Underwriter Platform

Property Underwriter is a two-tier application that helps real-estate investors analyze rental and flip opportunities. The backend exposes a REST API powered by FastAPI and SQLite persistence, while the frontend delivers an interactive underwriting experience with Next.js, TailwindCSS, and rich visual components. A legacy Streamlit UI is still available for rapid prototyping.

https://t-haskell.github.io/Property_Underwriter/

## Features

- **Rental analysis** – Computes NOI, debt service, cap rate, IRR, and suggested purchase price using configurable assumptions.
- **Flip analysis** – Projects ARV, carrying costs, profit margins, and purchase targets for renovation scenarios.
- **Data aggregation** – Normalizes results from multiple providers (RentCast, Estated, Redfin, Zillow, Rentometer, ATTOM, ClosingCorp, and mock fallbacks) into a single `PropertyData` snapshot with provenance metadata.
- **Address intelligence** – Offers search suggestions and structured address resolution using OpenStreetMap's Nominatim service to streamline data entry.
- **Persistence layer** – Stores fetched properties and completed analyses in SQLite (or any SQLAlchemy-compatible database) with versioned history and raw provider payload retention.
- **Modular architecture** – Business logic and calculations live in `src/core`, allowing independent evolution of the API surface, providers, and presentation layer.

## System Architecture

```
Property_Underwriter/
├─ src/
│  ├─ api/                    # FastAPI app, request/response schemas, persistence wiring
│  ├─ core/                   # Domain models and financial calculations
│  ├─ services/               # Providers, analysis orchestration, address lookup, caching
│  ├─ ui/                     # Streamlit components (legacy)
│  └─ utils/                  # Config, logging, currency helpers
├─ frontend/                  # Next.js 13 app with hooks, components, and API client
├─ tests/                     # Pytest suite for core calculations, services, persistence
├─ run_api.sh                 # Convenience launcher for the FastAPI development server
├─ run.sh                     # Legacy Streamlit launcher
└─ requirements.txt           # Python dependencies
```

### Backend (FastAPI)
- Entry point: `src/api/main.py`
- REST endpoints for health checks, address suggestions, property fetching, and rental/flip analyses.
- SQLite-backed persistence managed by `src/services/persistence.py` with simple configuration via `DATABASE_URL`.
- Uses provider adapters under `src/services/providers/` to enrich property snapshots.
- Logging, settings, and caching utilities reside in `src/utils`.

### Frontend (Next.js)
- Entry point: `frontend/app/page.tsx`
- Components under `frontend/components/` implement address autocomplete, assumption forms, and JSON payload viewers.
- API interactions go through `frontend/lib/api.ts`, which targets the FastAPI server (default `http://localhost:8000`).
- Styling delivered with TailwindCSS and motion utilities (`frontend/styles/`, `frontend/hooks/`).

### Legacy Streamlit UI
`src/app.py` provides the original Streamlit workflow. It exercises the same providers and analysis services, making it useful for quick demos or regression checks alongside the new web frontend.

## Configuration

1. Copy the backend environment template and populate provider keys as needed:
   ```bash
   cp .env.example .env
   # Edit .env to add API credentials
   ```
2. (Optional) Configure the frontend API base URL by creating `frontend/.env.local`:
   ```bash
   echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > frontend/.env.local
   ```
   Omit this step if you are running the backend on the default host/port.

### Supported Environment Variables
| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL for persistence | `sqlite:///property_underwriter.db` |
| `CACHE_TTL_MIN` | Minutes to cache provider responses | `60` |
| `PROVIDER_TIMEOUT_SEC` | Timeout (seconds) for provider HTTP calls | `10` |
| `USE_MOCK_PROVIDER_IF_NO_KEYS` | Fallback to deterministic mock data when providers are unconfigured | `true` |
| `GOOGLE_PLACES_API_KEY` | Optional Google Places key (Nominatim is used by default) | _unset_ |
| `ZILLOW_API_KEY`, `ZILLOW_BASE_URL` | Zillow / Bridge Interactive credentials | see `.env.example` |
| `RENTOMETER_API_KEY`, `RENTOMETER_BASE_URL` | Rentometer credentials | see `.env.example` |
| `ESTATED_API_KEY`, `ESTATED_BASE_URL` | Estated property API credentials | see `.env.example` |
| `RENTCAST_API_KEY`, `RENTCAST_BASE_URL` | RentCast rental data credentials | see `.env.example` |
| `REDFIN_API_KEY`, `REDFIN_BASE_URL`, `REDFIN_RAPIDAPI_HOST` | RapidAPI-backed Redfin client settings | see `.env.example` |
| `HUD_FMR_API_KEY`, `HUD_FMR_BASE_URL`, `HUD_FMR_CACHE_TTL_MIN` | HUD/open-data rent benchmark settings | `HUD_FMR_BASE_URL` defaults to HUD public FMR endpoint |
| `ENABLE_MARKETPLACE_SCRAPING`, `MARKETPLACE_SCRAPING_BASE_URL`, `MARKETPLACE_SCRAPING_API_KEY`, `MARKETPLACE_SCRAPING_TIMEOUT_SEC`, `MARKETPLACE_SCRAPING_MAX_RESULTS`, `MARKETPLACE_SCRAPING_MAX_RETRIES`, `MARKETPLACE_SCRAPING_BACKOFF_SEC` | Optional third-party scraping API integration for marketplace comps | `ENABLE_MARKETPLACE_SCRAPING=false` |
| `ATTOM_API_KEY`, `ATTOM_BASE_URL` | ATTOM property API credentials | see `.env.example` |
| `CLOSINGCORP_API_KEY`, `CLOSINGCORP_BASE_URL` | Closing cost data source credentials | see `.env.example` |

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Start the FastAPI backend
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"  # ensures local package resolution
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
This will create/update the SQLite database at `property_underwriter.db` (or the path specified by `DATABASE_URL`).

You can alternatively run `./run_api.sh` to perform the same setup and launch.

### 2. Start the Next.js frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000 in your browser. The development server proxies API calls to `http://localhost:8000` unless overridden by `NEXT_PUBLIC_API_BASE_URL`.

### 3. (Optional) Launch the Streamlit UI
```bash
./run.sh
```
The Streamlit experience remains useful for quick prototypes or side-by-side validation of the API results.

## API Overview

| Method & Path | Description |
| --- | --- |
| `GET /health` | Simple health probe. |
| `GET /api/places/suggest?query=` | Returns structured address suggestions from Nominatim. |
| `POST /api/places/resolve` | Resolves a suggestion payload to a normalized address. |
| `POST /api/property/fetch` | Fetches and merges provider data for an address. |
| `POST /api/analyze/rental` | Runs the rental underwriting workflow. |
| `POST /api/analyze/flip` | Runs the flip underwriting workflow. |

All endpoints exchange `Address`, `PropertyData`, and assumptions/result schemas defined in `src/api/schemas.py`.

## Testing & Quality

### Backend
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Linting
ruff check .

# Static type checks
mypy src tests

# Unit tests with coverage
pytest --cov=src --cov-report=xml --cov-fail-under=45

# Data provider unit tests (mocked HTTP)
pytest tests/test_data_providers.py
```

### Frontend
```bash
cd frontend
npm install
npm run lint
npm test           # Vitest unit tests
npm run storybook  # (optional) Component previews
```

## Development Tips
- Provider implementations live in `src/services/providers/`; they all implement `PropertyDataProvider` from `base.py`.
- `src/services/data_fetch.py` orchestrates provider calls, merges payloads, and persists results through `PropertyRepository`.
- Financial math is isolated in `src/core/calculations.py` and is thoroughly unit-tested; keep new calculations deterministic.
- Address search helpers reside in `src/services/nominatim_places.py`.
- To inspect stored data, open `property_underwriter.db` with any SQLite client; the schema tracks properties, provider sources, and analysis runs.

## Continuous Integration
The GitHub Actions workflow (`.github/workflows/ci.yml`) validates every push with Ruff, MyPy, Pytest coverage, and uploads the coverage report. Extend the pipeline if you introduce additional checks (e.g., frontend linting or tests).

