# Property Underwriter Platform – Project Summary

## 🎯 What We Built

An underwriting platform composed of a FastAPI backend, a modern Next.js frontend, and a legacy Streamlit app that all share the same analysis engine. Investors can fetch property data from multiple providers, run rental or flip scenarios, and persist their assumptions for later review.

- **REST API** serving underwriting workflows, address intelligence, and provider aggregation.
- **Next.js UI** for guided address entry, assumption tuning, and rich JSON inspection of provider payloads.
- **Streamlit prototype** that still exercises the same services for regression testing or rapid experimentation.

## 🏗️ Architecture Overview

```
Property_Underwriter/
├─ src/
│  ├─ api/                  # FastAPI app + Pydantic schemas
│  ├─ core/                 # Domain models and financial calculations
│  ├─ services/             # Providers, analysis orchestration, persistence
│  ├─ ui/                   # Streamlit widgets (legacy)
│  └─ utils/                # Logging, config, currency helpers
├─ frontend/                # Next.js 13 app (Tailwind, hooks, components)
├─ tests/                   # Pytest coverage for calculations/services/persistence
├─ run_api.sh               # FastAPI bootstrapper
├─ run.sh                   # Streamlit bootstrapper
└─ requirements.txt         # Python dependencies
```

Key integrations:
- **Provider adapters** (`src/services/providers/`) for Zillow, Rentometer, Estated, RentCast, Redfin (RapidAPI), ATTOM, ClosingCorp, and a deterministic mock provider.
- **Address discovery** via Nominatim (`src/services/nominatim_places.py`) for autocomplete and resolution.
- **SQLite persistence** managed by `src/services/persistence.py`, capturing properties, provider sources, and versioned analysis runs.

## 🚀 Quick Start

### Backend (FastAPI)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
The development server exposes the API on `http://localhost:8000` and initializes `property_underwriter.db` (configurable via `DATABASE_URL`).

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Browse to http://localhost:3000. The UI talks to the backend on port 8000 by default; override with `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` when needed.

### Streamlit (Optional)
```bash
./run.sh
```
Launches the original Streamlit interface, useful for quick demos or sanity checks.

## 🔧 Key Features

### 1. Rental Analysis
- Configurable purchase price, financing, vacancy, and reserves.
- Outputs NOI, debt service, cash flow, cap rate, IRR, and suggested purchase price.
- Persists each run with assumptions and results for auditability.

### 2. Flip Analysis
- Accepts renovation budgets, holding costs, and desired margins.
- Computes projected ARV, total costs, profit, and target price.
- Stores historical runs for comparison.

### 3. Data Integration & Persistence
- Merges property snapshots across configured providers while keeping source provenance.
- Caches provider payloads in SQLite to avoid duplicate calls and retain raw responses.
- Falls back to deterministic mock data when no API keys are configured.

### 4. Frontend Experience
- Address autocomplete backed by Nominatim suggestions with immediate normalization.
- Side-by-side summary and JSON payload explorer for merged property data and raw provider responses.
- Distinct forms for rental vs. flip assumptions with sensible defaults.

## 📊 Sample Data Flow
1. User searches for an address; Nominatim suggestions populate form fields.
2. Frontend calls `POST /api/property/fetch`; backend aggregates provider data and persists a snapshot.
3. User adjusts assumptions and triggers `POST /api/analyze/rental` or `/api/analyze/flip`.
4. Backend computes results via `src/services/analysis_service.py` and returns a typed response, which is stored alongside the property.

## 🧪 Testing
- **Backend**: `ruff check .`, `mypy src tests`, and `pytest --cov=src` validate style, types, and functionality.
- **Frontend**: `npm run lint`, `npm test`, and Storybook (`npm run storybook`) cover component, accessibility, and interaction checks.

## 🔮 Roadmap Notes
- Expand provider coverage with production credentials and error handling.
- Introduce caching/rate limiting for high-volume provider usage.
- Enhance frontend visualizations (charts, comparisons) and export options.
- Add authentication/authorization when multi-user access is required.

Keep this summary aligned with major architecture or workflow changes so contributors have an up-to-date mental model.

