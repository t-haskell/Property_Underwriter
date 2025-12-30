# Provider Guide

This guide documents the canonical provider interface used by the ingestion layer, how to build new providers, and how to add configuration safely.

## Canonical provider interface

The ingestion layer uses `BaseDataProvider` from `src/services/data_providers/base.py` and the `ProviderResult` model in `src/services/data_providers/models.py`.

Key concepts:

- **`BaseDataProvider`** defines `fetch_for_property(address)` and an optional `fetch_for_area(area_identifier)` method.
- **`ProviderMetadata`** includes `provider_name` (required string identifier), optional `provider_id`, `fetched_at` (timezone-aware), and optional `request_id`.
- **`ProviderResult`** encapsulates provider metadata, a typed payload (`PropertyDataPatch` and/or `AreaRentBenchmark` list), optional raw payload, and errors.
- **`PropertyDataPatch`** carries partial updates (beds, baths, rent estimates, etc.) plus metadata and provenance fields.

Exact `ProviderResult` fields:

- `metadata` (`ProviderMetadata`, required): contains `provider_name`, optional `provider_id`, `fetched_at`, and `request_id`.
- `property_data` (`PropertyDataPatch | None`): typed patch for property fields and provider-specific metadata.
- `area_rent_benchmarks` (`List[AreaRentBenchmark]`): optional area rent benchmarks.
- `raw_payload` (`Any | None`): raw upstream payload (logged/stored as JSON).
- `errors` (`List[str]`): any provider-level errors worth retaining.

## Minimal provider skeleton

```python
from __future__ import annotations

from typing import Optional

from src.core.models import Address
from src.services.data_providers.base import BaseDataProvider
from src.services.data_providers.models import (
    ProviderMetadata,
    ProviderResult,
    PropertyDataPatch,
)


class ExampleProvider(BaseDataProvider):
    name = "example"

    def fetch_for_property(self, address: Address) -> Optional[ProviderResult]:
        # TODO: call external API or data source
        patch = PropertyDataPatch(
            beds=3,
            baths=2,
            rent_estimate=2100,
            fields=["beds", "baths", "rent_estimate"],
            meta={"example_note": "sample data"},
        )
        return ProviderResult(
            metadata=ProviderMetadata(provider_name=self.name, provider_id="example-v1"),
            property_data=patch,
            raw_payload={"sample": True},
        )
```

## Provider registration

- Wire new providers into the aggregation service (see `_build_aggregation_service` in `src/services/data_fetch.py`).
- Confirm that the provider respects `ProviderResult` and returns `None` when no data is available.
- Add coverage under `tests/` with mocked HTTP responses.

## Adding env vars/config safely

1. Add new configuration values to `src/utils/config.py` and map them to environment variables.
2. Document the new values in `.env.example` and the README table.
3. Ensure defaults are safe for local development and do not require secrets.
4. Avoid introducing dependencies for configuration parsing—use the existing settings patterns.

## Checklist

- [ ] Implement `BaseDataProvider` methods and return `ProviderResult`.
- [ ] Attach provider metadata and `PropertyDataPatch` fields.
- [ ] Register provider in the aggregation service.
- [ ] Add tests and update documentation.
