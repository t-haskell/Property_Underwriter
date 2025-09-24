import json

from src.core.models import Address
from src.services.providers.closingcorp import ClosingcorpProvider


class _MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self):
        return self._data


def test_closingcorp_provider_maps_response(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        assert headers["Authorization"].startswith("Bearer ")
        return _MockResponse({"closing_costs": {"estimate": 8500, "taxes": 2500}})

    monkeypatch.setattr("requests.post", fake_post)

    provider = ClosingcorpProvider(api_key="token", base_url="https://example.com/closing")
    address = Address("1 Test", "Boston", "MA", "02108")

    data = provider.fetch(address)

    assert data is not None
    assert data.closing_cost_estimate == 8500
    assert data.meta["taxes"] == "2500"