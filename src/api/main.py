"""FastAPI application exposing Property Underwriter services."""

from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core.models import (
    Address,
    ApiSource,
    PropertyData,
    RentalAssumptions,
    FlipAssumptions,
)
from ..utils.logging import logger
from ..services.analysis_service import analyze_flip, analyze_rental
from ..services.data_fetch import fetch_property
from ..services.nominatim_places import (
    get_address_from_suggestion,
    get_place_suggestions,
)
from .schemas import (
    AddressPayload,
    FlipAnalysisRequest,
    FlipAnalysisResponse,
    FlipAssumptionsPayload,
    PropertyDataPayload,
    PropertyFetchRequest,
    PropertyFetchResponse,
    RentalAnalysisRequest,
    RentalAnalysisResponse,
    RentalAssumptionsPayload,
    SuggestionResolveRequest,
    SuggestionResolveResponse,
    SuggestionsResponse,
    Suggestion,
)

app = FastAPI(title="Property Underwriter API", version="0.1.0")

# Allow your frontend origins during development
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # be explicit when using credentials
    allow_credentials=True,          # set True only if you send cookies/auth headers
    allow_methods=["*"],             # or enumerate (e.g., ["GET","POST"])
    allow_headers=["*"],             # or enumerate needed headers
)

def _address_from_payload(payload: AddressPayload) -> Address:
    return Address(
        line1=payload.line1,
        city=payload.city,
        state=payload.state,
        zip=payload.zip,
    )


def _property_from_payload(payload: PropertyDataPayload) -> PropertyData:
    sources: List[ApiSource] = []
    for source in payload.sources:
        try:
            sources.append(ApiSource(source))
        except ValueError:
            # Ignore unknown sources but log-worthy in production
            continue

    return PropertyData(
        address=_address_from_payload(payload.address),
        beds=payload.beds,
        baths=payload.baths,
        sqft=payload.sqft,
        lot_sqft=payload.lot_sqft,
        year_built=payload.year_built,
        market_value_estimate=payload.market_value_estimate,
        rent_estimate=payload.rent_estimate,
        annual_taxes=payload.annual_taxes,
        closing_cost_estimate=payload.closing_cost_estimate,
        meta=dict(payload.meta or {}),
        sources=sources,
    )


def _property_to_response(pd: PropertyData) -> PropertyFetchResponse:
    address_payload = AddressPayload(
        line1=pd.address.line1,
        city=pd.address.city,
        state=pd.address.state,
        zip=pd.address.zip,
    )

    return PropertyFetchResponse(
        address=address_payload,
        beds=pd.beds,
        baths=pd.baths,
        sqft=pd.sqft,
        lot_sqft=pd.lot_sqft,
        year_built=pd.year_built,
        market_value_estimate=pd.market_value_estimate,
        rent_estimate=pd.rent_estimate,
        annual_taxes=pd.annual_taxes,
        closing_cost_estimate=pd.closing_cost_estimate,
        meta=pd.meta or {},
        sources=[source.value for source in pd.sources],
    )


def _rental_assumptions_from_payload(payload: RentalAssumptionsPayload) -> RentalAssumptions:
    return RentalAssumptions(
        down_payment_pct=payload.down_payment_pct,
        interest_rate_annual=payload.interest_rate_annual,
        loan_term_years=payload.loan_term_years,
        vacancy_rate_pct=payload.vacancy_rate_pct,
        maintenance_reserve_annual=payload.maintenance_reserve_annual,
        capex_reserve_annual=payload.capex_reserve_annual,
        insurance_annual=payload.insurance_annual,
        hoa_annual=payload.hoa_annual,
        property_mgmt_pct=payload.property_mgmt_pct,
        hold_period_years=payload.hold_period_years,
        target_cap_rate_pct=payload.target_cap_rate_pct,
        target_irr_pct=payload.target_irr_pct,
    )


def _flip_assumptions_from_payload(payload: FlipAssumptionsPayload) -> FlipAssumptions:
    return FlipAssumptions(
        down_payment_pct=payload.down_payment_pct,
        interest_rate_annual=payload.interest_rate_annual,
        loan_term_years=payload.loan_term_years,
        renovation_budget=payload.renovation_budget,
        hold_time_months=payload.hold_time_months,
        target_margin_pct=payload.target_margin_pct,
        closing_pct_buy=payload.closing_pct_buy,
        closing_pct_sell=payload.closing_pct_sell,
        arv_override=payload.arv_override,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/places/suggest", response_model=SuggestionsResponse)
def suggest_places(query: str) -> SuggestionsResponse:
    if not query or len(query.strip()) < 2:
        return SuggestionsResponse(suggestions=[])

    raw = get_place_suggestions(query.strip())
    suggestions = [
        Suggestion(
            description=item.get("description", ""),
            place_id=str(item.get("place_id", "")),
            lat=item.get("lat"),
            lon=item.get("lon"),
        )
        for item in raw
        if item.get("description")
    ]
    logger.info(f"Suggestions: {suggestions}")
    return SuggestionsResponse(suggestions=suggestions)


@app.post("/api/places/resolve", response_model=SuggestionResolveResponse)
def resolve_suggestion(payload: SuggestionResolveRequest) -> SuggestionResolveResponse:
    address = get_address_from_suggestion(payload.suggestion.dict())
    if not address:
        return SuggestionResolveResponse(address=None)

    return SuggestionResolveResponse(
        address=AddressPayload(
            line1=address.line1,
            city=address.city,
            state=address.state,
            zip=address.zip,
        )
    )


@app.post("/api/property/fetch", response_model=PropertyFetchResponse)
def property_fetch(payload: PropertyFetchRequest) -> PropertyFetchResponse:
    try:
        address = _address_from_payload(payload.address)
        property_data = fetch_property(address)
    except Exception as exc:  # pragma: no cover - surface to client
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if property_data is None:
        raise HTTPException(status_code=404, detail="Property not found")

    return _property_to_response(property_data)


@app.post("/api/analyze/rental", response_model=RentalAnalysisResponse)
def rental_analysis(payload: RentalAnalysisRequest) -> RentalAnalysisResponse:
    property_data = _property_from_payload(payload.property)
    assumptions = _rental_assumptions_from_payload(payload.assumptions)

    result = analyze_rental(property_data, assumptions, payload.purchase_price)

    return RentalAnalysisResponse(
        noi_annual=result.noi_annual,
        annual_debt_service=result.annual_debt_service,
        cash_flow_annual=result.cash_flow_annual,
        cap_rate_pct=result.cap_rate_pct,
        irr_pct=result.irr_pct,
        suggested_purchase_price=result.suggested_purchase_price,
    )


@app.post("/api/analyze/flip", response_model=FlipAnalysisResponse)
def flip_analysis(payload: FlipAnalysisRequest) -> FlipAnalysisResponse:
    property_data = _property_from_payload(payload.property)
    assumptions = _flip_assumptions_from_payload(payload.assumptions)

    result = analyze_flip(property_data, assumptions, payload.candidate_price)

    return FlipAnalysisResponse(
        arv=result.arv,
        total_costs=result.total_costs,
        suggested_purchase_price=result.suggested_purchase_price,
        projected_profit=result.projected_profit,
        margin_pct=result.margin_pct,
    )
