import pytest
from decimal import Decimal

from src.core.models import (
    Address,
    ApiSource,
    FlipAssumptions,
    PropertyData,
    RentalAssumptions,
)


def _base_address() -> dict[str, str]:
    return {
        "line1": "123 Main St",
        "city": "Boston",
        "state": "ma",
        "zip": "02108",
    }


def _base_property_kwargs() -> dict:
    return {
        "address": Address(**_base_address()),
        "beds": 3,
        "baths": 2,
        "sqft": 1600,
        "lot_sqft": 6000,
        "year_built": 1995,
        "market_value_estimate": 375000,
        "rent_estimate": 2450,
        "annual_taxes": 4200,
        "closing_cost_estimate": 8000,
        "meta": {"zpid": "123"},
        "sources": [ApiSource.MOCK],
    }


def _base_rental_kwargs() -> dict:
    return {
        "down_payment_pct": 20.0,
        "interest_rate_annual": 0.065,
        "loan_term_years": 30,
        "vacancy_rate_pct": 5.0,
        "maintenance_reserve_annual": 1200.0,
        "capex_reserve_annual": 1200.0,
        "insurance_annual": 1200.0,
        "hoa_annual": 0.0,
        "property_mgmt_pct": 8.0,
        "hold_period_years": 5,
        "target_cap_rate_pct": 6.0,
        "target_irr_pct": 12.0,
    }


def _base_flip_kwargs() -> dict:
    return {
        "down_payment_pct": 20.0,
        "interest_rate_annual": 0.065,
        "loan_term_years": 30,
        "renovation_budget": 60000.0,
        "hold_time_months": 6,
        "target_margin_pct": 0.10,
        "closing_pct_buy": 0.02,
        "closing_pct_sell": 0.06,
        "arv_override": None,
    }


@pytest.mark.parametrize(
    "model, kwargs",
    [
        (Address, _base_address()),
        (PropertyData, _base_property_kwargs()),
        (RentalAssumptions, _base_rental_kwargs()),
        (FlipAssumptions, _base_flip_kwargs()),
    ],
)
def test_models_accept_valid_payloads(model, kwargs):
    instance = model(**kwargs)
    assert instance


def test_address_state_is_uppercase():
    address = Address(**_base_address())
    assert address.state == "MA"


def test_property_data_rounds_monetary_fields():
    kwargs = _base_property_kwargs()
    kwargs.update(
        {
            "market_value_estimate": 375000.567,
            "rent_estimate": "2450.1349",
            "annual_taxes": Decimal("4200.345"),
            "closing_cost_estimate": 8000.999,
        }
    )

    property_data = PropertyData(**kwargs)

    assert property_data.market_value_estimate == pytest.approx(375000.57)
    assert property_data.rent_estimate == pytest.approx(2450.13, rel=0, abs=0.001)
    assert property_data.annual_taxes == pytest.approx(4200.35)
    assert property_data.closing_cost_estimate == pytest.approx(8001.0)


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("line1", ""),
        ("city", "\t"),
    ],
)
def test_address_rejects_blank_fields(field, bad_value):
    payload = _base_address()
    payload[field] = bad_value
    with pytest.raises(ValueError) as excinfo:
        Address(**payload)
    assert field in str(excinfo.value)



@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("market_value_estimate", -1),
        ("annual_taxes", -5),
        ("sqft", -100),
    ],
)
def test_property_data_rejects_invalid_numbers(field, bad_value):
    kwargs = _base_property_kwargs()
    kwargs[field] = bad_value
    with pytest.raises(ValueError) as excinfo:
        PropertyData(**kwargs)
    assert field in str(excinfo.value)


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("down_payment_pct", -1),
        ("interest_rate_annual", -0.1),
        ("loan_term_years", 0),
        ("hold_period_years", 0),
        ("maintenance_reserve_annual", -50),
    ],
)
def test_rental_assumptions_reject_invalid_payloads(field, bad_value):
    kwargs = _base_rental_kwargs()
    kwargs[field] = bad_value
    with pytest.raises(ValueError) as excinfo:
        RentalAssumptions(**kwargs)
    assert field in str(excinfo.value)


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("down_payment_pct", -1),
        ("loan_term_years", 0),
        ("hold_time_months", 0),
        ("renovation_budget", -1000),
        ("closing_pct_sell", -0.5),
    ],
)
def test_flip_assumptions_reject_invalid_payloads(field, bad_value):
    kwargs = _base_flip_kwargs()
    kwargs[field] = bad_value
    with pytest.raises(ValueError) as excinfo:
        FlipAssumptions(**kwargs)
    assert field in str(excinfo.value)
