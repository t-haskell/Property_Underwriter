import pytest
from src.core.models import ApiSource, Address, FlipAssumptions, PropertyData, RentalAssumptions
from src.services.analysis_service import analyze_flip, analyze_rental

@pytest.fixture
def sample_property():
    address = Address(line1="123 Main St", city="Boston", state="MA", zip="02108")
    return PropertyData(
        address=address,
        beds=3, baths=2, sqft=1600, lot_sqft=6000, year_built=1995,
        market_value_estimate=375000, rent_estimate=2450,
        annual_taxes=4200, closing_cost_estimate=8000,
        meta={}, sources=[ApiSource.MOCK]
    )

@pytest.fixture
def sample_rental_assumptions():
    return RentalAssumptions(
        down_payment_pct=20.0,
        interest_rate_annual=0.065,
        loan_term_years=30,
        vacancy_rate_pct=5.0,
        maintenance_reserve_annual=1200.0,
        capex_reserve_annual=1200.0,
        insurance_annual=1200.0,
        hoa_annual=0.0,
        property_mgmt_pct=8.0,
        hold_period_years=5,
        target_cap_rate_pct=6.0,
        target_irr_pct=12.0,
    )

@pytest.fixture
def sample_flip_assumptions():
    return FlipAssumptions(
        down_payment_pct=20.0,
        interest_rate_annual=0.065,
        loan_term_years=30,
        renovation_budget=60000.0,
        hold_time_months=6,
        target_margin_pct=0.10,
        closing_pct_buy=0.02,
        closing_pct_sell=0.06,
        arv_override=None,
    )

def test_analyze_rental(sample_property, sample_rental_assumptions):
    price = 350000.0
    result = analyze_rental(sample_property, sample_rental_assumptions, price)
    
    # Basic validation
    assert result.noi_annual > 0
    assert result.annual_debt_service > 0
    assert result.cap_rate_pct > 0
    assert result.suggested_purchase_price is not None
    
    # Test specific calculations
    # Annual rent: $2,450 * 12 = $29,400
    # NOI should be positive after expenses
    assert result.noi_annual > 10000  # Should be significantly positive
    
    # Cap rate should be reasonable (typically 3-10%)
    assert 3.0 <= result.cap_rate_pct <= 10.0

def test_analyze_rental_with_target_cap_rate(sample_property, sample_rental_assumptions):
    # Test with target cap rate
    sample_rental_assumptions.target_cap_rate_pct = 7.0
    price = 350000.0
    result = analyze_rental(sample_property, sample_rental_assumptions, price)
    
    assert result.suggested_purchase_price is not None
    assert result.suggested_purchase_price > 0

def test_analyze_flip(sample_property, sample_flip_assumptions):
    candidate_price = 250000.0
    result = analyze_flip(sample_property, sample_flip_assumptions, candidate_price)
    
    # Basic validation
    assert result.arv > 0
    assert result.total_costs > 0
    assert result.suggested_purchase_price > 0
    assert result.projected_profit >= 0
    assert result.margin_pct >= 0
    
    # ARV should match property market value estimate
    assert result.arv == sample_property.market_value_estimate
    
    # Total costs should include purchase price + renovation + soft costs
    assert result.total_costs > candidate_price + sample_flip_assumptions.renovation_budget

def test_analyze_flip_with_arv_override(sample_property, sample_flip_assumptions):
    # Test with ARV override
    sample_flip_assumptions.arv_override = 400000.0
    candidate_price = 250000.0
    result = analyze_flip(sample_property, sample_flip_assumptions, candidate_price)
    
    assert result.arv == 400000.0
    assert result.total_costs > candidate_price + sample_flip_assumptions.renovation_budget

def test_analyze_rental_edge_cases(sample_property):
    # Test with minimal assumptions
    minimal_assumptions = RentalAssumptions(
        down_payment_pct=100.0,  # Cash purchase
        interest_rate_annual=0.0,
        loan_term_years=30,
        vacancy_rate_pct=0.0,
        maintenance_reserve_annual=0.0,
        capex_reserve_annual=0.0,
        insurance_annual=0.0,
        hoa_annual=0.0,
        property_mgmt_pct=0.0,
        hold_period_years=1
    )
    
    result = analyze_rental(sample_property, minimal_assumptions, 350000.0)
    
    # With 100% down payment, debt service should be 0
    assert result.annual_debt_service == 0.0
    
    # Cash flow should equal NOI (no debt service, no reserves)
    assert abs(result.cash_flow_annual - result.noi_annual) < 0.01 