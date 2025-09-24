from __future__ import annotations
from typing import Optional, List
from core.models import PropertyData, RentalAssumptions, RentalResult, FlipAssumptions, FlipResult
from core.calculations import (
    noi_annual, annual_debt_service, rental_cash_flow, cap_rate_pct, irr,
    target_price_for_cap_rate, flip_suggested_purchase_price, soft_costs_from_pct, monthly_mortgage_payment
)

# CONSTANTS FOR OPEX
CONTROLLABLE = 1834



def analyze_rental(pd: PropertyData, a: RentalAssumptions, price: float) -> RentalResult:
    gross_rent = (pd.rent_estimate or 0.0) * 12
    opex = (pd.annual_taxes or 0.0) + a.insurance_annual + a.hoa_annual + CONTROLLABLE  #TODO: Need controllable operating expenses (i.e. payroll, admin, marketing, services, turnover cost, repairs & maintenances, and other categories )
    noi = noi_annual(gross_rent, a.vacancy_rate_pct, opex, a.property_mgmt_pct)
    loan_amt = price * (1 - a.down_payment_pct / 100)
    ads = annual_debt_service(loan_amt, a.interest_rate_annual, a.loan_term_years)
    cash_flow = rental_cash_flow(noi, ads, a.capex_reserve_annual)
    cap = cap_rate_pct(noi, price)
    # Simple IRR: down payment at t0, annual CF over hold, sale = price at end (placeholder)
    cf: List[float] = [-price * (a.down_payment_pct / 100)] + [cash_flow] * a.hold_period_years
    r_irr = irr(cf)
    suggested = target_price_for_cap_rate(noi, a.target_cap_rate_pct) if a.target_cap_rate_pct else None
    return RentalResult(noi, ads, cash_flow, cap, r_irr, suggested)

def analyze_flip(pd: PropertyData, a: FlipAssumptions, candidate_price: float) -> FlipResult:
    arv = a.arv_override or (pd.market_value_estimate or 0.0) # TODO Ensure market value is correct, like looking at comps for renovated/unrenovated
    #loan_amt = candidate_price * (1 - a.down_payment_pct / 100)
    loan_amt = 760306
    carry_costs = monthly_mortgage_payment(loan_amt, a.interest_rate_annual, a.loan_term_years)
    soft = soft_costs_from_pct(candidate_price, a.closing_pct_buy, a.closing_pct_sell, arv) + carry_costs * a.hold_time_months
    total_costs = candidate_price + a.renovation_budget + soft
    suggested = flip_suggested_purchase_price(arv, a.renovation_budget, soft, target_profit=(a.down_payment_pct / 100 * total_costs) * a.target_margin_pct / 100)
    print(f"soft: {soft} ")
    print(f"{soft_costs_from_pct(candidate_price, a.closing_pct_buy, a.closing_pct_sell, arv)} + {carry_costs * a.hold_time_months}")
    print(f"carry_costs: {carry_costs} ")
    total_costs = candidate_price + a.renovation_budget + soft
    print(f"total_costs: {total_costs}")
    profit = max(0.0, arv - total_costs)
    print(f"profit: {profit} / ({total_costs}-{loan_amt})")
    margin = 0.0 if arv == 0 else profit / (total_costs - loan_amt) # TODO: Fix this
    return FlipResult(arv, total_costs, suggested, profit, margin * 100) 