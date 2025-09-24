from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict

class ApiSource(str, Enum):
    ZILLOW = "zillow"
    RENTOMETER = "rentometer"
    ATTOM = "attom"
    CLOSINGCORP = "closingcorp"
    MOCK = "mock"

@dataclass
class Address:
    line1: str
    city: str
    state: str
    zip: str

@dataclass
class PropertyData:
    address: Address
    beds: Optional[float]
    baths: Optional[float]
    sqft: Optional[int]
    lot_sqft: Optional[int]
    year_built: Optional[int]
    market_value_estimate: Optional[float]
    rent_estimate: Optional[float]
    annual_taxes: Optional[float]
    closing_cost_estimate: Optional[float]
    meta: Dict[str, str]  # e.g., {"zpid": "..."}
    sources: List[ApiSource]

@dataclass
class RentalAssumptions:
    down_payment_pct: float
    interest_rate_annual: float
    loan_term_years: int
    vacancy_rate_pct: float
    maintenance_reserve_annual: float
    capex_reserve_annual: float
    insurance_annual: float
    hoa_annual: float
    property_mgmt_pct: float
    hold_period_years: int
    target_cap_rate_pct: Optional[float] = None
    target_irr_pct: Optional[float] = None

@dataclass
class FlipAssumptions:
    down_payment_pct: float
    interest_rate_annual: float
    loan_term_years: int
    renovation_budget: float
    hold_time_months: int
    target_margin_pct: float
    closing_pct_buy: float
    closing_pct_sell: float
    arv_override: Optional[float] = None

@dataclass
class RentalResult:
    noi_annual: float
    annual_debt_service: float
    cash_flow_annual: float
    cap_rate_pct: float
    irr_pct: Optional[float]
    suggested_purchase_price: Optional[float]

@dataclass
class FlipResult:
    arv: float
    total_costs: float
    suggested_purchase_price: float
    projected_profit: float
    margin_pct: float 