import pytest

from src.core.models import Address, ApiSource, PropertyData
from src.services import data_fetch
from src.services.providers.mock import MockProvider


class DummyProvider(MockProvider):
    def __init__(self, data: PropertyData):
        self._data = data

    def fetch(self, address: Address):
        return self._data


def test_merge_prefers_newer_values():
    address = Address(line1="123 Main", city="Boston", state="MA", zip="02108")
    a = PropertyData(
        address=address,
        beds=3,
        baths=2,
        sqft=1500,
        lot_sqft=None,
        year_built=None,
        market_value_estimate=300000,
        rent_estimate=2000,
        annual_taxes=3500,
        closing_cost_estimate=None,
        meta={"source_a": "1"},
        sources=[ApiSource.MOCK],
    )
    b = PropertyData(
        address=address,
        beds=None,
        baths=2.5,
        sqft=1550,
        lot_sqft=4000,
        year_built=1990,
        market_value_estimate=320000,
        rent_estimate=None,
        annual_taxes=None,
        closing_cost_estimate=8000,
        meta={"source_b": "2"},
        sources=[ApiSource.ZILLOW],
    )

    merged = data_fetch.merge(a, b)

    assert merged.beds == 3  # original retained
    assert merged.baths == 2.5
    assert merged.lot_sqft == 4000
    assert merged.market_value_estimate == 320000
    assert merged.closing_cost_estimate == 8000
    assert merged.meta == {"source_a": "1", "source_b": "2"}
    assert merged.sources == [ApiSource.MOCK, ApiSource.ZILLOW]


def test_fetch_property_uses_configured_providers(monkeypatch):
    address = Address(line1="123 Main", city="Boston", state="MA", zip="02108")

    data_one = PropertyData(
        address=address,
        beds=3,
        baths=2,
        sqft=1500,
        lot_sqft=None,
        year_built=1992,
        market_value_estimate=310000,
        rent_estimate=2200,
        annual_taxes=3600,
        closing_cost_estimate=None,
        meta={},
        sources=[ApiSource.ZILLOW],
    )

    provider = DummyProvider(data_one)

    monkeypatch.setattr(data_fetch, "_configured_providers", lambda: [provider])
    monkeypatch.setattr(data_fetch, "MockProvider", lambda: pytest.fail("Mock fallback should not be used"))

    result = data_fetch.fetch_property(address)
    assert result is not None
    assert result.sources == [ApiSource.ZILLOW]


def test_fetch_property_falls_back_to_mock(monkeypatch):
    address = Address(line1="456 Elm", city="Boston", state="MA", zip="02108")

    class NullProvider(MockProvider):
        def fetch(self, address: Address):
            return None

    fallback_data = PropertyData(
        address=address,
        beds=2,
        baths=1,
        sqft=900,
        lot_sqft=None,
        year_built=None,
        market_value_estimate=None,
        rent_estimate=1800,
        annual_taxes=None,
        closing_cost_estimate=None,
        meta={"source": "mock"},
        sources=[ApiSource.MOCK],
    )

    class _Mock(MockProvider):
        def fetch(self, address: Address):
            return fallback_data

    monkeypatch.setattr(data_fetch, "_configured_providers", lambda: [NullProvider()])
    monkeypatch.setattr(data_fetch, "MockProvider", lambda: _Mock())

    result = data_fetch.fetch_property(address)

    assert result == fallback_data
