from __future__ import annotations
from typing import List

from ..core.models import FlipAssumptions, FlipResult, PropertyData, RentalAssumptions, RentalResult
from ..core.calculations import (
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

def analyze_rental(pd: PropertyData, a: RentalAssumptions, price: float) -> RentalResult:
    gross_rent = (pd.rent_estimate or 0.0) * 12
    operating_expenses = (
        (pd.annual_taxes or 0.0)
        + a.insurance_annual
        + a.hoa_annual
        + a.maintenance_reserve_annual
    )
    noi = noi_annual(gross_rent, a.vacancy_rate_pct, operating_expenses, a.property_mgmt_pct)
    loan_amt = price * (1 - a.down_payment_pct / 100)
    ads = annual_debt_service(loan_amt, a.interest_rate_annual, a.loan_term_years)
    reserves = a.capex_reserve_annual
    cash_flow = rental_cash_flow(noi, ads, reserves)
    cap = cap_rate_pct(noi, price)
    sale_proceeds = pd.market_value_estimate or price
    payments_made = min(a.hold_period_years * 12, a.loan_term_years * 12)
    remaining_balance = remaining_loan_balance(loan_amt, a.interest_rate_annual, a.loan_term_years, payments_made)
    cash_flows: List[float] = [-price * (a.down_payment_pct / 100)]
    if a.hold_period_years > 1:
        cash_flows.extend([cash_flow] * (a.hold_period_years - 1))
    final_cash_flow = cash_flow + sale_proceeds - remaining_balance
    cash_flows.append(final_cash_flow)
    r_irr = irr(cash_flows)
    suggested = target_price_for_cap_rate(noi, a.target_cap_rate_pct) if a.target_cap_rate_pct else None
    return RentalResult(noi, ads, cash_flow, cap, r_irr, suggested)

def analyze_flip(pd: PropertyData, a: FlipAssumptions, candidate_price: float) -> FlipResult:
    arv = a.arv_override or (pd.market_value_estimate or 0.0)
    loan_amount = candidate_price * (1 - a.down_payment_pct / 100)
    monthly_carry = monthly_mortgage_payment(loan_amount, a.interest_rate_annual, a.loan_term_years)
    carry_costs = monthly_carry * a.hold_time_months
    soft = soft_costs_from_pct(candidate_price, a.closing_pct_buy, a.closing_pct_sell, arv) + carry_costs
    total_costs = candidate_price + a.renovation_budget + soft
    target_profit = arv * a.target_margin_pct if a.target_margin_pct else 0.0
    suggested = flip_suggested_purchase_price(arv, a.renovation_budget, soft, target_profit)
    profit = max(0.0, arv - total_costs)
    margin = 0.0 if total_costs == 0 else (profit / total_costs) * 100
    return FlipResult(arv, total_costs, suggested, profit, margin)
