import json

from src.core.models import Address
from src.services.providers.attom import AttomProvider


class _MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self):
        return self._data


def test_attom_provider_maps_response(monkeypatch):
    attom_payload = {
        "property": [
            {
                "building": {
                    "rooms": {"beds": 3, "bathsTotal": 2.5},
                    "size": {"universalSize": 1800},
                },
                "lot": {"lotSize2": 5500},
                "summary": {"yearBuilt": 1990, "legal1": "Lot 12"},
                "identifier": {"apn": "123456789", "fips": "25025"},
                "assessment": {
                    "market": {"mktTtlValue": 400000},
                    "tax": {"taxAmt": 4200},
                },
            }
        ]
    }

    def fake_get(url, headers=None, params=None, timeout=None):
        assert headers["apikey"] == "token"
        return _MockResponse(attom_payload)

    monkeypatch.setattr("requests.get", fake_get)

    provider = AttomProvider(api_key="token", base_url="https://example.com")
    address = Address(line1="1 Test", city="Boston", state="MA", zip="02108")

    data = provider.fetch(address)

    assert data is not None
    assert data.beds == 3
    assert data.sqft == 1800
    assert data.lot_sqft == 5500
    assert data.annual_taxes == 4200
