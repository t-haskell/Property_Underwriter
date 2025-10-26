import json

from src.core.models import Address
from src.services.providers.rentometer import RentometerProvider


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


def test_rentometer_provider_maps_average(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert "summary" in url
        assert params["api_key"] == "token"
        return _MockResponse({"data": {"average": 2450, "median": 2400, "sample_size": 50}})

    monkeypatch.setattr("src.services.providers.rentometer.httpx.get", fake_get)

    provider = RentometerProvider(api_key="token", base_url="https://example.com", default_bedrooms=3)
    address = Address(line1="1 Test", city="Boston", state="MA", zip="02108")

    data = provider.fetch(address)

    assert data is not None
    assert data.rent_estimate == 2450
    assert data.meta["median"] == "2400"
    assert data.sources[0].value == "rentometer"
    assert json.loads(data.meta["rentometer_raw"]) == {
        "data": {"average": 2450, "median": 2400, "sample_size": 50}
    }
