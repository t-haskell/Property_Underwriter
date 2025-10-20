from __future__ import annotations
from typing import List, Optional


def monthly_mortgage_payment(principal: float, annual_rate: float, term_years: int, interest_only: bool = False) -> float:
    """Fixed-rate monthly payment. ``annual_rate`` should be expressed as a decimal (e.g. 0.065)."""

    if principal <= 0:
        return 0.0

    total_payments = max(term_years, 0) * 12
    if total_payments == 0:
        return principal

    monthly_rate = annual_rate / 12

    if annual_rate == 0:
        return principal / total_payments

    if interest_only:
        return principal * monthly_rate

    factor = (1 + monthly_rate) ** total_payments
    return principal * (monthly_rate * factor) / (factor - 1)


def remaining_loan_balance(principal: float, annual_rate: float, term_years: int, payments_made_months: int) -> float:
    """Outstanding balance after a number of payments."""

    if principal <= 0:
        return 0.0

    total_payments = max(term_years, 0) * 12
    payments_made = max(0, min(payments_made_months, total_payments))

    if total_payments == 0:
        return 0.0

    if annual_rate == 0:
        payment = principal / total_payments
        remaining = principal - payment * payments_made
        return max(remaining, 0.0)

    monthly_rate = annual_rate / 12
    payment = monthly_mortgage_payment(principal, annual_rate, term_years)
    balance = principal * (1 + monthly_rate) ** payments_made - payment * (((1 + monthly_rate) ** payments_made - 1) / monthly_rate)
    return max(balance, 0.0)

# Validated
def noi_annual(gross_rent_annual: float, vacancy_rate_pct: float,
               opex_annual: float, mgmt_pct: float) -> float:
    effective = gross_rent_annual * (1 - vacancy_rate_pct / 100)
    mgmt = effective * (mgmt_pct / 100)
    return effective - (opex_annual + mgmt)

# Validated
def cap_rate_pct(noi_annual: float, price: float) -> float:
    return 0.0 if price == 0 else (noi_annual / price) * 100

# Validated
def annual_debt_service(principal: float, annual_rate: float, term_years: int) -> float:
    return monthly_mortgage_payment(principal, annual_rate, term_years) * 12

# Validated
def debt_service_ratio(noi_annual: float, ads: float) -> float: #ads = annual debt service 
    return 0.0 if noi_annual == 0 else (ads / noi_annual) * 100

# Validated
def rental_cash_flow(noi_annual: float, ads: float, reserves_annual: float) -> float:
    return noi_annual - ads - reserves_annual

# Validated
def target_price_for_cap_rate(noi_annual: float, target_cap_rate_pct: float) -> float:
    return 0.0 if target_cap_rate_pct <= 0 else noi_annual / (target_cap_rate_pct / 100)

# Validated
def irr(cash_flows: List[float], guess: float = 0.1, max_iter: int = 100) -> Optional[float]:
    """Simple Newton-based IRR; return None if no convergence."""
    try:
        r = guess
        for _ in range(max_iter):
            npv = sum(cf / (1 + r) ** i for i, cf in enumerate(cash_flows))
            d_npv = sum(-i * cf / (1 + r) ** (i + 1) for i, cf in enumerate(cash_flows) if i > 0)
            if abs(npv) < 1e-6:
                return r * 100
            r -= npv / d_npv if d_npv != 0 else 0.0
        return None
    except Exception:
        return None

# Validated
def flip_suggested_purchase_price(arv: float, reno: float, soft_costs: float,
                                  target_profit: float) -> float:
    """Back out price from ARV: price = ARV - reno - soft_costs - target_profit."""
    return max(0.0, arv - reno - soft_costs - target_profit)

def soft_costs_from_pct(price: float, closing_buy_pct: float, closing_sell_pct: float,
                        arv: float) -> float:
    """Compute soft costs from fractional percentages (e.g. 0.02 for 2%)."""
    return (price * closing_buy_pct) + (arv * closing_sell_pct)
