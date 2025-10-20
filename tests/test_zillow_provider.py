import json

from src.core.models import Address
from src.services.providers.zillow import ZillowProvider


class _MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    @property
    def is_error(self):
        return self.status_code >= 400

    def json(self):
        return self._data


def test_zillow_provider_maps_response(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(url)
        if url.endswith("/properties"):
            return _MockResponse({"properties": [{"zpid": "12345"}]})
        if url.endswith("/properties/12345"):
            return _MockResponse(
                {
                    "zpid": "12345",
                    "bedrooms": 3,
                    "bathrooms": 2.5,
                    "finishedSqFt": 1600,
                    "lotSizeSqFt": 6000,
                    "yearBuilt": 1995,
                    "zestimate": 375000,
                    "rentZestimate": 2450,
                    "taxAssessment": 4200,
                    "lastUpdated": "2023-09-01",
                    "zestimateConfidence": 7,
                }
            )
        raise AssertionError(f"Unexpected URL {url}")

    monkeypatch.setattr("src.services.providers.zillow.httpx.get", fake_get)

    provider = ZillowProvider(api_key="token", base_url="https://example.com", timeout=5)
    address = Address(line1="123 Main St", city="Boston", state="MA", zip="02108")

    data = provider.fetch(address)

    assert data is not None
    assert data.beds == 3
    assert data.baths == 2.5
    assert data.market_value_estimate == 375000
    assert data.rent_estimate == 2450
    assert data.meta["zpid"] == "12345"
    assert len(calls) == 2
