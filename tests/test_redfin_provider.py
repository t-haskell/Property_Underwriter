import json

from src.core.models import Address, ApiSource
from src.services.providers.redfin import RedfinProvider


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


def test_redfin_provider_parses_response(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        return _MockResponse(
            {
                "status": "OK",
                "result": {
                    "propertyDetail": {
                        "beds": 4,
                        "baths": 3.5,
                        "squareFeet": 2450,
                        "lotSizeSqFt": 7400,
                        "yearBuilt": 2005,
                        "redfinEstimate": 585000,
                        "rentEstimate": 3200,
                        "annualTax": 6100,
                        "propertyId": "R-12345",
                        "url": "https://www.redfin.com/some-listing",
                    }
                },
            }
        )

    monkeypatch.setattr("src.services.providers.redfin.httpx.get", fake_get)

    provider = RedfinProvider(api_key="token", base_url="https://example.com", host="example.com")
    address = Address(line1="123 Main St", city="Boston", state="MA", zip="02108")

    data = provider.fetch(address)

    assert data is not None
    assert data.sources == [ApiSource.REDFIN]
    assert data.beds == 4
    assert data.baths == 3.5
    assert data.sqft == 2450
    assert data.lot_sqft == 7400
    assert data.year_built == 2005
    assert data.market_value_estimate == 585000
    assert data.rent_estimate == 3200
    assert data.annual_taxes == 6100
    assert data.meta["redfin_property_id"] == "R-12345"
    assert data.meta["redfin_url"] == "https://www.redfin.com/some-listing"
    assert json.loads(data.meta["redfin_raw"]) == {
        "status": "OK",
        "result": {
            "propertyDetail": {
                "beds": 4,
                "baths": 3.5,
                "squareFeet": 2450,
                "lotSizeSqFt": 7400,
                "yearBuilt": 2005,
                "redfinEstimate": 585000,
                "rentEstimate": 3200,
                "annualTax": 6100,
                "propertyId": "R-12345",
                "url": "https://www.redfin.com/some-listing",
            }
        },
    }

    assert captured["url"] == "https://example.com/detailsByAddress"
    assert captured["params"] == {"address": "123 Main St, Boston, MA 02108"}
    assert captured["headers"]["X-RapidAPI-Key"] == "token"
    assert captured["headers"]["X-RapidAPI-Host"] == "example.com"
