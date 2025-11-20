# Data Ingestion Layer Plan

## Goals
- Introduce a pluggable data provider abstraction for property-level and area-level enrichments.
- Prioritise free/open data (e.g., HUD Fair Market Rents) with optional marketplace comps via third-party scraping APIs behind feature flags.
- Preserve provenance (provider, timestamp, raw payload reference) for every contributed field and merge results deterministically.

## Architecture Outline
1. **Provider Contracts**
   - Add `BaseDataProvider` with `fetch_for_property` and `fetch_for_area` returning typed `ProviderResult` objects.
   - Define shared models (`ProviderMetadata`, `PropertyDataPatch`, `AreaRentBenchmark`, `ProviderResult`) capturing normalized data and provenance-friendly raw payloads.

2. **Providers**
   - Implement `HudFmrProvider` to fetch area-level rent benchmarks by ZIP/metro from configurable HUD/open-data endpoint with caching and timeout handling.
   - Add `MarketplaceCompsProvider` (scraping API integration) guarded by `ENABLE_MARKETPLACE_SCRAPING` and API settings; includes backoff and clear ToS docstrings.

3. **Aggregation**
   - Introduce `DataAggregationService` to orchestrate:
     - Existing spine providers (Zillow/RentCast/etc.) via thin adapter to `PropertyDataPatch`.
     - Open-data providers for benchmarks and auxiliary fields.
     - Optional marketplace comps.
   - Merge into `PropertyData`, respecting precedence and embedding provenance entries in a structured list plus meta raw payload pointers.

4. **Integration**
   - Wire aggregation into `services.data_fetch.fetch_property` (backward compatible API) and persistence meta handling for provenance storage.
   - Expose configuration via environment-driven settings (HUD/marketplace endpoints, flags, timeouts, caching TTLs).

5. **Testing & Docs**
   - Add unit tests for provider parsing/error paths and aggregation precedence using mocked HTTP responses.
   - Document provider usage and configuration in `docs/data_providers.md` and update README with new env vars/test guidance.
