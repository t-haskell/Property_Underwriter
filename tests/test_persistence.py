from datetime import datetime

from src.core.models import (
    Address,
    ApiSource,
    FlipResult,
    PropertyData,
    RentalAssumptions,
    RentalResult,
)
from src.services.data_fetch import fetch_property
from src.services.persistence import configure, get_repository


def build_property() -> PropertyData:
    address = Address(line1="123 Main St", city="Austin", state="TX", zip="78701")
    return PropertyData(
        address=address,
        beds=3,
        baths=2.5,
        sqft=1800,
        lot_sqft=7200,
        year_built=1985,
        market_value_estimate=425000,
        rent_estimate=2450,
        annual_taxes=4850,
        closing_cost_estimate=None,
        meta={"initial": "true"},
        sources=[ApiSource.ESTATED],
    )


def test_property_repository_round_trip(tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'repo.db'}"
    configure(db_url)
    repository = get_repository()

    property_data = build_property()
    saved = repository.upsert_property(property_data)

    assert saved.market_value_estimate == property_data.market_value_estimate
    assert saved.meta["initial"] == "true"
    assert saved.sources == [ApiSource.ESTATED]

    updated = property_data.model_copy(update={
        "market_value_estimate": 430000,
        "meta": {"initial": "false", "confidence": "0.82"},
        "sources": [ApiSource.ESTATED, ApiSource.MOCK],
    })
    repository.upsert_property(updated)

    fetched = repository.get_property(property_data.address)
    assert fetched is not None
    assert fetched.market_value_estimate == 430000
    assert fetched.meta["initial"] == "false"
    assert fetched.meta["confidence"] == "0.82"
    assert set(fetched.sources) == {ApiSource.ESTATED, ApiSource.MOCK}

    rental_assumptions = RentalAssumptions(
        down_payment_pct=25.0,
        interest_rate_annual=0.06,
        loan_term_years=30,
        vacancy_rate_pct=5.0,
        maintenance_reserve_annual=1200.0,
        capex_reserve_annual=1200.0,
        insurance_annual=900.0,
        hoa_annual=0.0,
        property_mgmt_pct=7.0,
        hold_period_years=5,
        target_cap_rate_pct=None,
        target_irr_pct=None,
    )
    rental_result = RentalResult(
        noi_annual=18000.0,
        annual_debt_service=12000.0,
        cash_flow_annual=6000.0,
        cap_rate_pct=5.1423,
        cash_on_cash_return_pct=9.75,
        irr_pct=11.5,
        suggested_purchase_price=320000.0,
    )

    repository.record_analysis(
        fetched,
        analysis_type="rental",
        purchase_price=300000.0,
        assumptions=rental_assumptions.model_dump(),
        result=rental_result,
    )

    flip_result = FlipResult(
        arv=450000.0,
        total_costs=360000.0,
        suggested_purchase_price=290000.0,
        projected_profit=90000.0,
        margin_pct=25.0,
    )

    repository.record_analysis(
        fetched,
        analysis_type="flip",
        purchase_price=310000.0,
        assumptions={"note": "demo"},
        result=flip_result,
    )

    history_all = repository.list_analyses(property_data.address)
    assert len(history_all) == 2
    assert {entry.analysis_type for entry in history_all} == {"rental", "flip"}

    rental_only = repository.list_analyses(property_data.address, analysis_type="rental")
    assert len(rental_only) == 1
    rental_snapshot = rental_only[0]
    assert rental_snapshot.purchase_price == 300000.0
    assert rental_snapshot.result["noi_annual"] == rental_result.noi_annual
    assert isinstance(rental_snapshot.created_at, datetime)


def test_fetch_property_uses_cached_data(tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'cache.db'}"
    configure(db_url)
    repository = get_repository()

    property_data = build_property()
    repository.upsert_property(property_data)

    fetched = fetch_property(property_data.address, use_mock_if_empty=False)
    assert fetched is not None
    assert fetched.market_value_estimate == property_data.market_value_estimate
    assert fetched.sources == property_data.sources
