"""API integration-style tests for FastAPI app."""

from __future__ import annotations

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.api import main
from src.utils.config import Settings
from src.core.models import (
    Address,
    ApiSource,
    FlipResult,
    PropertyData,
    RentalResult,
)


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client bound to the application under test."""
    return TestClient(main.app, raise_server_exceptions=False)


def test_create_app_configures_cors_and_database(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    configured: dict[str, str] = {}

    def fake_configure(database_url: str) -> None:
        configured["database_url"] = database_url

    monkeypatch.setattr(main, "configure", fake_configure)

    database_url = f"sqlite:///{tmp_path/'custom.db'}"
    settings = Settings(
        DATABASE_URL=database_url,
        API_ALLOWED_ORIGINS="https://example.com, http://localhost:4000/",
    )

    app = main.create_app(settings)
    with TestClient(app):
        pass

    assert configured["database_url"] == database_url
    cors = next((m for m in app.user_middleware if m.cls is CORSMiddleware), None)
    assert cors is not None
    assert cors.kwargs["allow_origins"] == ["https://example.com", "http://localhost:4000"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok"}


def test_suggest_places_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    calls = {}

    def fake_get_place_suggestions(query: str, limit: int):
        calls["args"] = (query, limit)
        return [
            {
                "description": "123 Main St, Springfield, IL",
                "place_id": 42,
                "street": "123 Main St",
                "city": "Springfield",
                "state": "il",
                "zip": "62704",
                "lat": "39.7817",
                "lon": "-89.6501",
            },
            {
                "description": "",
                "place_id": 99,
            },
        ]

    monkeypatch.setattr(main, "get_place_suggestions", fake_get_place_suggestions)

    response = client.get("/api/places/suggest", params={"query": " Springfield  ", "limit": 50})

    assert calls["args"] == ("Springfield", 10)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "suggestions": [
            {
                "description": "123 Main St, Springfield, IL",
                "place_id": "42",
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip": "62704",
                "lat": "39.7817",
                "lon": "-89.6501",
            }
        ]
    }


def test_suggest_places_short_query_returns_empty(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_get_place_suggestions(query: str, limit: int):  # pragma: no cover - sanity check
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(main, "get_place_suggestions", fake_get_place_suggestions)

    response = client.get("/api/places/suggest", params={"query": "a"})

    assert called is False
    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_resolve_suggestion_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_get_address_from_suggestion(payload: dict) -> Address:
        assert payload == {
            "description": "123 Main St",
            "place_id": "abc",
            "street": None,
            "city": None,
            "state": None,
            "zip": None,
            "lat": None,
            "lon": None,
        }
        return Address(line1="123 Main St", city="Springfield", state="IL", zip="62704")

    monkeypatch.setattr(main, "get_address_from_suggestion", fake_get_address_from_suggestion)

    response = client.post(
        "/api/places/resolve",
        json={
            "suggestion": {
                "description": "123 Main St",
                "place_id": "abc",
                "street": None,
                "city": None,
                "state": None,
                "zip": None,
                "lat": None,
                "lon": None,
            }
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "address": {
            "line1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704",
        }
    }


def test_resolve_suggestion_not_found(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(main, "get_address_from_suggestion", lambda payload: None)

    response = client.post(
        "/api/places/resolve",
        json={
            "suggestion": {
                "description": "Missing",
                "place_id": "missing",
                "street": None,
                "city": None,
                "state": None,
                "zip": None,
                "lat": None,
                "lon": None,
            }
        },
    )

    assert response.status_code == 200
    assert response.json() == {"address": None}


def _property_payload() -> dict:
    return {
        "address": {
            "line1": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704",
        },
        "beds": 3,
        "baths": 2,
        "sqft": 1800,
        "lot_sqft": 6000,
        "year_built": 1990,
        "market_value_estimate": 325000.0,
        "rent_estimate": 2200.0,
        "annual_taxes": 4500.0,
        "closing_cost_estimate": 7500.0,
        "meta": {"zpid": "123456"},
        "sources": ["zillow", "rentometer"],
    }


def _property_data() -> PropertyData:
    return PropertyData(
        address=Address(line1="123 Main St", city="Springfield", state="IL", zip="62704"),
        beds=3,
        baths=2,
        sqft=1800,
        lot_sqft=6000,
        year_built=1990,
        market_value_estimate=325000.0,
        rent_estimate=2200.0,
        annual_taxes=4500.0,
        closing_cost_estimate=7500.0,
        meta={"zpid": "123456"},
        sources=[ApiSource.ZILLOW, ApiSource.RENTOMETER],
    )


def test_property_fetch_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(main, "fetch_property", lambda address: _property_data())

    response = client.post("/api/property/fetch", json={"address": _property_payload()["address"]})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == _property_payload()


def test_property_fetch_not_found(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(main, "fetch_property", lambda address: None)

    response = client.post("/api/property/fetch", json={"address": _property_payload()["address"]})

    assert response.status_code == 404
    assert response.json() == {"detail": "Property not found"}


def test_property_fetch_dependency_error(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_fetch_property(address: Address):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main, "fetch_property", fake_fetch_property)

    response = client.post("/api/property/fetch", json={"address": _property_payload()["address"]})

    assert response.status_code == 500
    assert response.json() == {"detail": "provider unavailable"}


def _rental_assumptions_payload() -> dict:
    return {
        "down_payment_pct": 0.2,
        "interest_rate_annual": 0.05,
        "loan_term_years": 30,
        "vacancy_rate_pct": 0.05,
        "maintenance_reserve_annual": 1200.0,
        "capex_reserve_annual": 1500.0,
        "insurance_annual": 900.0,
        "hoa_annual": 0.0,
        "property_mgmt_pct": 0.08,
        "hold_period_years": 5,
        "target_cap_rate_pct": 6.5,
        "target_irr_pct": 12.0,
    }


def _rental_result() -> RentalResult:
    return RentalResult(
        noi_annual=18000.0,
        annual_debt_service=12000.0,
        cash_flow_annual=6000.0,
        cap_rate_pct=6.0,
        cash_on_cash_return_pct=10.5,
        irr_pct=11.5,
        suggested_purchase_price=310000.0,
    )


def test_rental_analysis_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_analyze_rental(property_data, assumptions, purchase_price):
        assert property_data.address.line1 == "123 Main St"
        assert assumptions.down_payment_pct == 0.2
        assert purchase_price == 300000.0
        return _rental_result()

    monkeypatch.setattr(main, "analyze_rental", fake_analyze_rental)

    response = client.post(
        "/api/analyze/rental",
        json={
            "property": _property_payload(),
            "assumptions": _rental_assumptions_payload(),
            "purchase_price": 300000.0,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "noi_annual": 18000.0,
        "annual_debt_service": 12000.0,
        "cash_flow_annual": 6000.0,
        "cap_rate_pct": 6.0,
        "cash_on_cash_return_pct": 10.5,
        "irr_pct": 11.5,
        "suggested_purchase_price": 310000.0,
    }


def test_rental_analysis_dependency_error(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_analyze_rental(property_data, assumptions, purchase_price):
        raise ValueError("calculation failure")

    monkeypatch.setattr(main, "analyze_rental", fake_analyze_rental)

    response = client.post(
        "/api/analyze/rental",
        json={
            "property": _property_payload(),
            "assumptions": _rental_assumptions_payload(),
            "purchase_price": 300000.0,
        },
    )

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Internal Server Error"


def _flip_assumptions_payload() -> dict:
    return {
        "down_payment_pct": 0.25,
        "interest_rate_annual": 0.06,
        "loan_term_years": 15,
        "renovation_budget": 45000.0,
        "hold_time_months": 9,
        "target_margin_pct": 0.2,
        "closing_pct_buy": 0.02,
        "closing_pct_sell": 0.03,
        "arv_override": None,
    }


def _flip_result() -> FlipResult:
    return FlipResult(
        arv=420000.0,
        total_costs=360000.0,
        suggested_purchase_price=310000.0,
        projected_profit=60000.0,
        margin_pct=0.19,
    )


def test_flip_analysis_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_analyze_flip(property_data, assumptions, candidate_price):
        assert property_data.sqft == 1800
        assert assumptions.renovation_budget == 45000.0
        assert candidate_price == 305000.0
        return _flip_result()

    monkeypatch.setattr(main, "analyze_flip", fake_analyze_flip)

    response = client.post(
        "/api/analyze/flip",
        json={
            "property": _property_payload(),
            "assumptions": _flip_assumptions_payload(),
            "candidate_price": 305000.0,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "arv": 420000.0,
        "total_costs": 360000.0,
        "suggested_purchase_price": 310000.0,
        "projected_profit": 60000.0,
        "margin_pct": 0.19,
    }


def test_flip_analysis_dependency_error(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_analyze_flip(property_data, assumptions, candidate_price):
        raise RuntimeError("flip engine offline")

    monkeypatch.setattr(main, "analyze_flip", fake_analyze_flip)

    response = client.post(
        "/api/analyze/flip",
        json={
            "property": _property_payload(),
            "assumptions": _flip_assumptions_payload(),
            "candidate_price": 305000.0,
        },
    )

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Internal Server Error"
