"""Pydantic schemas for the Property Underwriter REST API."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AddressPayload(BaseModel):
    line1: str = Field(..., description="Street address line 1")
    city: str = Field(..., description="City name")
    state: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    zip: str = Field(..., min_length=5, max_length=10, description="ZIP or postal code")

    @validator("state")
    def _state_upper(cls, value: str) -> str:
        return value.upper()


class PropertyDataPayload(BaseModel):
    address: AddressPayload
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    market_value_estimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    annual_taxes: Optional[float] = None
    closing_cost_estimate: Optional[float] = None
    meta: Dict[str, str] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)


class PropertyFetchRequest(BaseModel):
    address: AddressPayload


class PropertyFetchResponse(PropertyDataPayload):
    """Response shape matches PropertyDataPayload."""


class RentalAssumptionsPayload(BaseModel):
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
    closing_costs_pct: float = 3.0
    target_cap_rate_pct: Optional[float] = None
    target_irr_pct: Optional[float] = None


class RentalAnalysisRequest(BaseModel):
    property: PropertyDataPayload
    assumptions: RentalAssumptionsPayload
    purchase_price: float


class RentalAnalysisResponse(BaseModel):
    noi_annual: float
    annual_debt_service: float
    cash_flow_annual: float
    cap_rate_pct: float
    cash_on_cash_return_pct: float
    irr_pct: Optional[float]
    suggested_purchase_price: Optional[float]


class FlipAssumptionsPayload(BaseModel):
    down_payment_pct: float
    interest_rate_annual: float
    loan_term_years: int
    renovation_budget: float
    hold_time_months: int
    target_margin_pct: float
    closing_pct_buy: float
    closing_pct_sell: float
    arv_override: Optional[float] = None


class FlipAnalysisRequest(BaseModel):
    property: PropertyDataPayload
    assumptions: FlipAssumptionsPayload
    candidate_price: float


class FlipAnalysisResponse(BaseModel):
    arv: float
    total_costs: float
    suggested_purchase_price: float
    projected_profit: float
    margin_pct: float


class Suggestion(BaseModel):
    description: str
    place_id: str
    street: Optional[str] = Field(default=None, description="Street address line returned by Nominatim")
    city: Optional[str] = Field(default=None, description="City or locality name")
    state: Optional[str] = Field(default=None, min_length=2, max_length=2, description="Two-letter state code if available")
    zip: Optional[str] = Field(default=None, description="ZIP or postal code")
    lat: Optional[str] = None
    lon: Optional[str] = None

    @validator("state")
    def _state_upper(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value


class SuggestionsResponse(BaseModel):
    suggestions: List[Suggestion]


class SuggestionResolveRequest(BaseModel):
    suggestion: Suggestion


class SuggestionResolveResponse(BaseModel):
    address: Optional[AddressPayload] = None
