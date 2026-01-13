from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


NumberLike = Union[int, float, Decimal, str]


class DomainModel(BaseModel):
    """Base model that re-raises validation issues as ``ValueError``.

    Centralising validation in one place ensures that any consumer of the
    domain models receives a consistent ``ValueError`` when supplied payloads do
    not satisfy the invariants we declare.  This mirrors the behaviour of the
    previous dataclasses while gaining the expressiveness of Pydantic.
    """

    model_config = ConfigDict(validate_assignment=True, str_strip_whitespace=True)

    def __init__(self, **data):  # type: ignore[override]
        try:
            super().__init__(**data)
        except ValidationError as exc:  # pragma: no cover - exercised in tests
            messages = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
            raise ValueError(messages) from exc


def _coerce_number(
    value: NumberLike | None,
    *,
    field_name: str,
    allow_none: bool,
    minimum: float | None = None,
    decimals: int | None = None,
) -> Optional[float]:
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"{field_name} is required")

    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError(f"{field_name} cannot be blank")

    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if minimum is not None and number < minimum:
        comparison = "negative" if minimum == 0 else f"less than {minimum}"
        raise ValueError(f"{field_name} cannot be {comparison}")

    if decimals is not None:
        number = round(number, decimals)

    return number


def _coerce_non_negative_float(
    value: NumberLike | None,
    *,
    field_name: str,
    allow_none: bool = False,
    decimals: int | None = None,
) -> Optional[float]:
    return _coerce_number(
        value,
        field_name=field_name,
        allow_none=allow_none,
        minimum=0.0,
        decimals=decimals,
    )


def _coerce_positive_int(value: NumberLike, *, field_name: str) -> int:
    number = _coerce_number(value, field_name=field_name, allow_none=False, minimum=1)
    assert number is not None  # for mypy
    if not float(number).is_integer():
        raise ValueError(f"{field_name} must be a whole number")
    return int(number)


def _coerce_non_negative_int(
    value: NumberLike | None,
    *,
    field_name: str,
    allow_none: bool = True,
) -> Optional[int]:
    number = _coerce_number(
        value,
        field_name=field_name,
        allow_none=allow_none,
        minimum=0.0,
    )
    if number is None:
        return None
    if not float(number).is_integer():
        raise ValueError(f"{field_name} must be a whole number")
    return int(number)


class ApiSource(str, Enum):
    ZILLOW = "zillow"
    RENTOMETER = "rentometer"
    ATTOM = "attom"
    CLOSINGCORP = "closingcorp"
    ESTATED = "estated"
    RENTCAST = "rentcast"
    REDFIN = "redfin"
    MD_IMAP = "md_imap"
    MASS_GIS = "mass_gis"
    MOCK = "mock"
    HUD = "hud_fmr"
    MARKETPLACE = "marketplace_comps"


class Address(DomainModel):
    line1: str
    city: str
    state: str
    zip: str

    @field_validator("line1", "city", "state", "zip")
    @classmethod
    def _ensure_not_blank(cls, value: str, info):
        if value == "":
            raise ValueError(f"{info.field_name} cannot be blank")
        return value

    @field_validator("state")
    @classmethod
    def _normalise_state(cls, value: str) -> str:
        return value.upper()


class PropertyData(DomainModel):
    address: Address
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
    sources: List[ApiSource] = Field(default_factory=list)
    provenance: List["SourceAttribution"] = Field(default_factory=list)

    @field_validator("beds", "baths", mode="before")
    @classmethod
    def _validate_optional_unit_counts(cls, value: NumberLike | None, info):
        return _coerce_non_negative_float(value, field_name=info.field_name, allow_none=True)

    @field_validator("sqft", "lot_sqft", "year_built", mode="before")
    @classmethod
    def _validate_optional_ints(cls, value: NumberLike | None, info):
        return _coerce_non_negative_int(value, field_name=info.field_name, allow_none=True)

    @field_validator(
        "market_value_estimate",
        "rent_estimate",
        "annual_taxes",
        "closing_cost_estimate",
        mode="before",
    )
    @classmethod
    def _validate_monetary_fields(cls, value: NumberLike | None, info):
        return _coerce_non_negative_float(
            value,
            field_name=info.field_name,
            allow_none=True,
            decimals=2,
        )


class SourceAttribution(DomainModel):
    provider: str
    fields: List[str] = Field(default_factory=list)
    fetched_at: datetime
    request_id: Optional[str] = None
    raw_reference: Optional[str] = None

    @field_validator("provider")
    @classmethod
    def _validate_provider(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("provider cannot be blank")
        return value

    @field_validator("fields")
    @classmethod
    def _validate_fields(cls, value: List[str]) -> List[str]:
        cleaned = [item for item in value if item]
        if not cleaned:
            raise ValueError("fields cannot be empty")
        return cleaned


class RentalAssumptions(DomainModel):
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

    @field_validator("down_payment_pct", "vacancy_rate_pct", "property_mgmt_pct", "closing_costs_pct")
    @classmethod
    def _validate_percentage(cls, value: NumberLike, info):
        result = _coerce_non_negative_float(value, field_name=info.field_name)
        assert result is not None
        return round(result, 4)

    @field_validator("interest_rate_annual")
    @classmethod
    def _validate_interest(cls, value: NumberLike):
        result = _coerce_non_negative_float(value, field_name="interest_rate_annual")
        assert result is not None
        return round(result, 6)

    @field_validator("maintenance_reserve_annual", "capex_reserve_annual", "insurance_annual", "hoa_annual", mode="before")
    @classmethod
    def _validate_annual_costs(cls, value: NumberLike, info):
        result = _coerce_non_negative_float(value, field_name=info.field_name, decimals=2)
        assert result is not None
        return result

    @field_validator("loan_term_years")
    @classmethod
    def _validate_loan_term(cls, value: NumberLike):
        return _coerce_positive_int(value, field_name="loan_term_years")

    @field_validator("hold_period_years")
    @classmethod
    def _validate_hold_period(cls, value: NumberLike):
        return _coerce_positive_int(value, field_name="hold_period_years")

    @field_validator("target_cap_rate_pct", "target_irr_pct", mode="before")
    @classmethod
    def _validate_optional_percentage(cls, value: NumberLike | None, info):
        return _coerce_non_negative_float(
            value,
            field_name=info.field_name,
            allow_none=True,
            decimals=4,
        )


class FlipAssumptions(DomainModel):
    down_payment_pct: float
    interest_rate_annual: float
    loan_term_years: int
    renovation_budget: float
    hold_time_months: int
    target_margin_pct: float
    closing_pct_buy: float
    closing_pct_sell: float
    arv_override: Optional[float] = None

    @field_validator("down_payment_pct", "target_margin_pct", "closing_pct_buy", "closing_pct_sell")
    @classmethod
    def _validate_percentages(cls, value: NumberLike, info):
        result = _coerce_non_negative_float(value, field_name=info.field_name)
        assert result is not None
        return round(result, 4)

    @field_validator("interest_rate_annual")
    @classmethod
    def _validate_flip_interest(cls, value: NumberLike):
        result = _coerce_non_negative_float(value, field_name="interest_rate_annual")
        assert result is not None
        return round(result, 6)

    @field_validator("loan_term_years")
    @classmethod
    def _validate_flip_loan_term(cls, value: NumberLike):
        return _coerce_positive_int(value, field_name="loan_term_years")

    @field_validator("hold_time_months")
    @classmethod
    def _validate_hold_time(cls, value: NumberLike):
        number = _coerce_positive_int(value, field_name="hold_time_months")
        if number <= 0:
            raise ValueError("hold_time_months must be positive")
        return number

    @field_validator("renovation_budget", mode="before")
    @classmethod
    def _validate_renovation_budget(cls, value: NumberLike):
        result = _coerce_non_negative_float(value, field_name="renovation_budget", decimals=2)
        assert result is not None
        return result

    @field_validator("arv_override", mode="before")
    @classmethod
    def _validate_optional_arv(cls, value: NumberLike | None):
        return _coerce_non_negative_float(
            value,
            field_name="arv_override",
            allow_none=True,
            decimals=2,
        )


class RentalResult(DomainModel):
    noi_annual: float
    annual_debt_service: float
    cash_flow_annual: float
    cap_rate_pct: float
    cash_on_cash_return_pct: float
    irr_pct: Optional[float]
    suggested_purchase_price: Optional[float]

    @field_validator("annual_debt_service", mode="before")
    @classmethod
    def _validate_debt_service(cls, value: NumberLike):
        result = _coerce_non_negative_float(value, field_name="annual_debt_service", decimals=2)
        assert result is not None
        return result

    @field_validator("noi_annual", "cash_flow_annual", mode="before")
    @classmethod
    def _validate_flows(cls, value: NumberLike, info):
        result = _coerce_number(value, field_name=info.field_name, allow_none=False, decimals=2)
        assert result is not None
        return result

    @field_validator("cap_rate_pct", "cash_on_cash_return_pct", mode="before")
    @classmethod
    def _validate_cap_rate(cls, value: NumberLike, info):
        result = _coerce_number(value, field_name=info.field_name, allow_none=False, decimals=4)
        assert result is not None
        return result

    @field_validator("irr_pct", mode="before")
    @classmethod
    def _validate_optional_irr(cls, value: NumberLike | None):
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("irr_pct must be numeric")
        return float(value)

    @field_validator("suggested_purchase_price", mode="before")
    @classmethod
    def _validate_optional_suggested(cls, value: NumberLike | None):
        return _coerce_non_negative_float(
            value,
            field_name="suggested_purchase_price",
            allow_none=True,
            decimals=2,
        )


class FlipResult(DomainModel):
    arv: float
    total_costs: float
    suggested_purchase_price: float
    projected_profit: float
    margin_pct: float

    @field_validator("arv", "total_costs", "suggested_purchase_price", "projected_profit", mode="before")
    @classmethod
    def _validate_flip_totals(cls, value: NumberLike, info):
        result = _coerce_non_negative_float(value, field_name=info.field_name, decimals=2)
        assert result is not None
        return result

    @field_validator("margin_pct", mode="before")
    @classmethod
    def _validate_margin(cls, value: NumberLike):
        result = _coerce_non_negative_float(value, field_name="margin_pct", decimals=4)
        assert result is not None
        return result

