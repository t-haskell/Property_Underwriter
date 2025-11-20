# Data Providers & Aggregation

This repository now exposes a dedicated ingestion layer for both free/open data and optional marketplace scraping APIs. Providers share a common contract and can be composed via the `DataAggregationService`.

## Provider Abstraction
- `src/services/data_providers/base.py` defines `BaseDataProvider` with `fetch_for_property`/`fetch_for_area` methods returning a `ProviderResult`.
- Common data structures live in `src/services/data_providers/models.py` (property patches, area rent benchmarks, provider metadata, provenance helpers).
- Legacy providers under `src/services/providers/` are wrapped automatically when building the aggregation service.

## Available Providers
- **HUD Fair Market Rents (`HudFmrProvider`)**
  - Pulls area-level rent benchmarks using ZIP/state inputs.
  - Configured via `HUD_FMR_BASE_URL`, `HUD_FMR_API_KEY` (optional), `HUD_FMR_CACHE_TTL_MIN`, and `PROVIDER_TIMEOUT_SEC`.
- **Marketplace comps (`MarketplaceCompsProvider`)**
  - Calls compliant third-party scraping APIs (e.g., Apify) for fresh listings/comps.
  - Guarded by `ENABLE_MARKETPLACE_SCRAPING`; additional settings: `MARKETPLACE_SCRAPING_BASE_URL`, `MARKETPLACE_SCRAPING_API_KEY`, `MARKETPLACE_SCRAPING_TIMEOUT_SEC`, `MARKETPLACE_SCRAPING_MAX_RESULTS`, `MARKETPLACE_SCRAPING_MAX_RETRIES`, `MARKETPLACE_SCRAPING_BACKOFF_SEC`.
  - Includes retry/backoff for rate limits and returns average rent estimates plus raw comps in metadata.

## Aggregation
- `DataAggregationService` orchestrates primary providers (Zillow/RentCast/etc.), open-data providers (HUD), and optional marketplace comps.
- Merge rules:
  - Primary providers run first and populate the core `PropertyData` fields.
  - Open-data providers fill gaps and attach rent benchmarks without overriding populated values.
  - Marketplace comps are optional refinements; they default to non-destructive updates.
- Source provenance is captured in `PropertyData.provenance` with provider, timestamp, fields, and raw payload reference. Raw payloads and rent benchmarks are stored in `PropertyData.meta` as JSON strings.

## Adding Providers
1. Implement `BaseDataProvider` returning a `ProviderResult` with `PropertyDataPatch` and/or area data.
2. Wire configuration through `src/utils/config.py` (environment variables only).
3. Register the provider in `_build_aggregation_service` (or a new factory) and add tests mocking HTTP responses.
