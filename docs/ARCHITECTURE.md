# Architecture

This document captures the current layout, data flow, and near-term refactor direction for the Property Underwriter platform.

## Folder map

```
Property_Underwriter/
├─ src/
│  ├─ api/         # FastAPI endpoints, request/response schemas, dependency wiring
│  ├─ core/        # Domain models and underwriting calculations
│  ├─ services/    # Provider orchestration, persistence, data ingestion utilities
│  └─ utils/       # Settings, logging, configuration helpers
├─ frontend/       # Next.js UI and API client
└─ tests/          # Pytest coverage for services, core, and API surface
```

## Current data flow

1. **Frontend** submits a property lookup from the Next.js app.
2. The backend receives the request at **`POST /api/property/fetch`** (`src/api/main.py`).
3. The handler calls **`services/data_fetch.fetch_property`**, which normalizes the address and decides whether to reuse cached data.
4. `fetch_property` builds the provider aggregation service and calls **provider aggregation** to collect primary, open-data, and marketplace provider results.
5. The aggregation result is persisted via **`PropertyRepository.upsert_property`** (`src/services/persistence.py`).
6. The API responds with the merged `PropertyData` snapshot.

## Refactor roadmap

- Unify legacy providers in `src/services/providers/` with the newer ingestion layer in `src/services/data_providers/`.
- Consolidate provider configuration, metadata, and provenance handling behind a single aggregation service.
- Reduce duplicate provider wiring in API/service entry points so the fetch pipeline has a single canonical path.

These changes will be incremental and should preserve the current `fetch_property` contract and API responses.
