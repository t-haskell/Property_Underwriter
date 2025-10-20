import httpx
import pytest

from src.core.models import Address, ApiSource
from src.services.providers.estated import EstatedProvider


class MockResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = ""

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def sample_address() -> Address:
    return Address(line1="123 Main St", city="Austin", state="TX", zip="78701")


def test_estated_provider_parses_success(monkeypatch, sample_address):
    payload = {
        "status": "success",
        "data": {
            "property": {
                "identifier": "abc-123",
                "structure": {
                    "beds": 3,
                    "baths": 2.5,
                    "total_square_feet": 1800,
                    "year_built": 1985,
                },
                "land": {"lot_square_feet": 7200},
                "valuation": {
                    "market": {
                        "value": {
                            "estimate": 425000,
                            "low": 410000,
                            "high": 440000,
                            "confidence": 0.82,
                        },
                        "updated": "2024-03-01",
                    },
                    "rent": {"estimate": 2450, "updated": "2024-02-15"},
                    "tax": {"amount": 4850},
                },
            }
        },
    }

    def fake_get(url, params, timeout):  # pragma: no cover - assertions via test
        assert "token" in params
        assert params["address"] == sample_address.line1
        return MockResponse(payload)

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = EstatedProvider(api_key="token")
    result = provider.fetch(sample_address)

    assert result is not None
    assert result.beds == 3
    assert result.baths == 2.5
    assert result.sqft == 1800
    assert result.lot_sqft == 7200
    assert result.market_value_estimate == 425000
    assert result.rent_estimate == 2450
    assert result.annual_taxes == 4850
    assert result.sources == [ApiSource.ESTATED]
    assert result.meta["estated_identifier"] == "abc-123"
    assert result.meta["valuation_low"] == "410000.0"
    assert result.meta["valuation_high"] == "440000.0"
    assert result.meta["rent_estimate_date"] == "2024-02-15"


def test_estated_provider_handles_failure(monkeypatch, sample_address):
    def fake_get(url, params, timeout):
        return MockResponse({"status": "error", "message": "not found"}, status_code=404)

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = EstatedProvider(api_key="token")
    result = provider.fetch(sample_address)
    assert result is None


def test_estated_provider_handles_invalid_json(monkeypatch, sample_address):
    class BrokenResponse(MockResponse):
        def json(self):
            raise ValueError("boom")

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: BrokenResponse({}, status_code=200))

    provider = EstatedProvider(api_key="token")
    assert provider.fetch(sample_address) is None
