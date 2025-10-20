from src.core.calculations import (
    annual_debt_service,
    cap_rate_pct,
    flip_suggested_purchase_price,
    irr,
    monthly_mortgage_payment,
    noi_annual,
    remaining_loan_balance,
    rental_cash_flow,
    soft_costs_from_pct,
    target_price_for_cap_rate,
)

def test_monthly_mortgage_payment():
    # Test case: $300k loan, 6% annual rate, 30 years
    payment = monthly_mortgage_payment(300000, 0.06, 30)
    assert abs(payment - 1798.65) < 1.0  # Allow small rounding differences
    
    # Test zero interest rate
    payment = monthly_mortgage_payment(300000, 0.0, 30)
    assert payment == 300000 / (30 * 12)

    # Interest only
    interest_only_payment = monthly_mortgage_payment(300000, 0.06, 30, interest_only=True)
    assert abs(interest_only_payment - (300000 * 0.06 / 12)) < 1e-6

def test_noi_annual():
    # Test case: $30k annual rent, 5% vacancy, $8k opex, 8% mgmt
    noi = noi_annual(30000, 5.0, 8000, 8.0)
    expected = 30000 * 0.95 - 8000 - (30000 * 0.95 * 0.08)
    assert abs(noi - expected) < 0.01

def test_cap_rate_pct():
    # Test case: $15k NOI, $300k price
    cap_rate = cap_rate_pct(15000, 300000)
    assert cap_rate == 5.0
    
    # Test zero price
    cap_rate = cap_rate_pct(15000, 0)
    assert cap_rate == 0.0

def test_annual_debt_service():
    # Test case: $300k loan, 6% annual rate, 30 years
    ads = annual_debt_service(300000, 0.06, 30)
    monthly = monthly_mortgage_payment(300000, 0.06, 30)
    assert abs(ads - monthly * 12) < 0.01

def test_rental_cash_flow():
    # Test case: $15k NOI, $12k debt service, $2k reserves
    cf = rental_cash_flow(15000, 12000, 2000)
    assert cf == 1000

def test_target_price_for_cap_rate():
    # Test case: $15k NOI, 5% target cap rate
    price = target_price_for_cap_rate(15000, 5.0)
    assert price == 300000
    
    # Test zero target cap rate
    price = target_price_for_cap_rate(15000, 0.0)
    assert price == 0.0

def test_irr():
    # Test case: Simple cash flows
    cf = [-1000, 200, 200, 200, 200, 1200]  # 5-year investment
    irr_val = irr(cf)
    assert irr_val is not None
    assert irr_val > 0  # Should be positive for this cash flow

def test_flip_suggested_purchase_price():
    # Test case: $400k ARV, $50k reno, $20k soft costs, $40k target profit
    price = flip_suggested_purchase_price(400000, 50000, 20000, 40000)
    assert price == 290000

def test_soft_costs_from_pct():
    # Test case: $300k price, 2% buy closing, 6% sell closing, $400k ARV
    soft = soft_costs_from_pct(300000, 0.02, 0.06, 400000)
    expected = 300000 * 0.02 + 400000 * 0.06
    assert abs(soft - expected) < 0.01 


def test_remaining_loan_balance():
    principal = 300000
    rate = 0.05
    term_years = 30
    # After 60 payments (5 years) the balance should be less than the principal
    balance = remaining_loan_balance(principal, rate, term_years, 60)
    assert balance < principal

    # Zero interest case reduces linearly
    linear_balance = remaining_loan_balance(principal, 0.0, term_years, 60)
    expected_balance = principal - (principal / (term_years * 12)) * 60
    assert abs(linear_balance - expected_balance) < 1e-6
