import json
import time

import httpx

from src.core.models import Address, ApiSource
from src.services.data_providers import (
    DataAggregationService,
    HudFmrProvider,
    MarketplaceCompsProvider,
    ProviderMetadata,
    ProviderResult,
    PropertyDataPatch,
)
from src.services.data_providers.base import BaseDataProvider
from src.services.data_providers.models import AreaIdentifier, AreaRentBenchmark


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _StaticProvider(BaseDataProvider):
    def __init__(self, name: str, result: ProviderResult | None):
        self.name = name
        self._result = result

    def fetch_for_property(self, address: Address):  # pragma: no cover - trivial
        return self._result


def test_hud_fmr_provider_parses_and_caches(monkeypatch):
    calls: list[dict] = []

    def fake_get(url, params=None, timeout=None):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return _DummyResponse({"year": 2024, "fmr": {"0": 900, "1": 1100}})

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = HudFmrProvider(
        base_url="https://example.test/fmr", api_key=None, timeout=2, cache_ttl_min=10
    )
    address = Address(line1="1 Main", city="Austin", state="TX", zip="78701")

    first = provider.fetch_for_property(address)
    second = provider.fetch_for_property(address)

    assert first is not None
    assert second is not None
    assert len(first.area_rent_benchmarks) == 2
    # Cache should avoid a second HTTP call
    assert len(calls) == 1


def test_marketplace_comps_provider_handles_rate_limits(monkeypatch):
    attempts: list[int] = []

    def fake_post(url, json=None, headers=None, timeout=None):
        attempts.append(int(time.time()))
        if len(attempts) == 1:
            return httpx.Response(429, request=httpx.Request("POST", url))
        return httpx.Response(
            200,
            json=[
                {"address": "123", "rent": 1200, "beds": 2, "baths": 1.5, "distance": 0.5},
                {"address": "456", "rent": 1400, "beds": 3, "baths": 2, "distance": 1.1},
            ],
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = MarketplaceCompsProvider(
        base_url="https://example.test/api",
        api_key="token",
        enabled=True,
        timeout=1,
        max_results=5,
        max_retries=1,
        backoff_seconds=0,
    )

    address = Address(line1="1 Main", city="Austin", state="TX", zip="78701")
    result = provider.fetch_for_property(address)

    assert result is not None
    assert result.property_data is not None
    assert result.property_data.rent_estimate == 1300.0
    assert json.loads(result.property_data.meta["marketplace_comps"])[0]["address"] == "123"


def test_data_aggregation_merges_sources_and_benchmarks():
    address = Address(line1="1 Main", city="Austin", state="TX", zip="78701")

    primary_result = ProviderResult(
        metadata=ProviderMetadata(provider_name=ApiSource.ZILLOW.value),
        property_data=PropertyDataPatch(
            beds=3,
            rent_estimate=2000,
            fields=["beds", "rent_estimate"],
            raw_reference="zillow_raw",
        ),
        raw_payload={"id": "z"},
    )

    open_data_result = ProviderResult(
        metadata=ProviderMetadata(provider_name=ApiSource.HUD.value),
        area_rent_benchmarks=[
            AreaRentBenchmark(
                area=AreaIdentifier(zip=address.zip, state=address.state),
                bedroom_count=2,
                rent=1500,
                year=2024,
            )
        ],
    )

    aggregator = DataAggregationService(
        primary_providers=[],
        open_data_providers=[
            _StaticProvider(ApiSource.ZILLOW.value, primary_result),
            _StaticProvider(ApiSource.HUD.value, open_data_result),
        ],
        marketplace_provider=None,
    )

    aggregated = aggregator.aggregate(address)

    assert aggregated.beds == 3
    assert aggregated.rent_estimate == 2000
    assert ApiSource.ZILLOW in aggregated.sources
    assert any(src.provider == ApiSource.ZILLOW.value for src in aggregated.provenance)
    benchmarks = json.loads(aggregated.meta.get("rent_benchmarks", "[]"))
    assert benchmarks[0]["provider"] == ApiSource.HUD.value
