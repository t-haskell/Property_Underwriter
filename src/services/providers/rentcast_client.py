from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import httpx

from ...core.models import Address
from ..property_merging import NormalizedPropertyRecord, ProviderName
from ...utils.logging import logger
from .config import rentcast


@dataclass(slots=True)
class RentcastProperty:
    address: Address
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    market_value_estimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    annual_taxes: Optional[float] = None
    property_type: Optional[str] = None
    raw: Dict[str, Any] | None = None


class RentcastClient:
    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = rentcast.DEFAULT_TIMEOUT_SEC) -> None:
        self.api_key = api_key
        self.base_url = (base_url or rentcast.BASE_URL).rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {"X-Api-Key": self.api_key, "accept": "application/json"}

    def get_by_address(self, address: Address) -> Optional[RentcastProperty]:
        params = {
            "address": address.line1,
            "city": address.city,
            "state": address.state,
            "zipCode": address.zip,
        }
        try:
            response = httpx.get(
                f"{self.base_url}{rentcast.PROPERTY_ENDPOINT}",
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            logger.warning("Rentcast property fetch failed: %s", exc)
            return None

        payload = response.json()
        if not isinstance(payload, list) or not payload:
            return None
        return self._map_record(payload[0])

    def _map_record(self, payload: Dict[str, Any]) -> RentcastProperty:
        market_value = None
        tax_assessments = payload.get("taxAssessments") or {}
        if isinstance(tax_assessments, dict):
            latest_year = _latest_numeric_key(tax_assessments)
            if latest_year:
                assessment = tax_assessments.get(latest_year) or {}
                if isinstance(assessment, dict):
                    market_value = _safe_number(assessment.get("value"))

        property_taxes = payload.get("propertyTaxes") or {}
        annual_taxes = None
        if isinstance(property_taxes, dict):
            latest_tax_year = _latest_numeric_key(property_taxes)
            if latest_tax_year:
                taxes = property_taxes.get(latest_tax_year) or {}
                if isinstance(taxes, dict):
                    annual_taxes = _safe_number(taxes.get("total"))

        return RentcastProperty(
            address=Address(
                line1=str(payload.get("address", "")),
                city=str(payload.get("city", "")),
                state=str(payload.get("state", "")),
                zip=str(payload.get("zipCode", "")),
            ),
            beds=_safe_number(payload.get(rentcast.FIELD_MAPPINGS.get("beds", ""))),
            baths=_safe_number(payload.get(rentcast.FIELD_MAPPINGS.get("baths", ""))),
            sqft=_safe_int(payload.get(rentcast.FIELD_MAPPINGS.get("sqft", ""))),
            lot_sqft=_safe_int(payload.get(rentcast.FIELD_MAPPINGS.get("lot_sqft", ""))),
            year_built=_safe_int(payload.get(rentcast.FIELD_MAPPINGS.get("year_built", ""))),
            market_value_estimate=market_value,
            rent_estimate=_safe_number(payload.get(rentcast.FIELD_MAPPINGS.get("rent_estimate", ""))),
            annual_taxes=annual_taxes,
            property_type=_safe_str(payload.get("propertyType")),
            raw=payload,
        )


def normalize_rentcast(record: RentcastProperty) -> NormalizedPropertyRecord:
    meta: Dict[str, str] = {}
    if record.property_type:
        meta["propertyType"] = record.property_type

    return NormalizedPropertyRecord(
        provider=ProviderName.RENTCAST,
        fetched_at=datetime.now(UTC),
        address=record.address,
        beds=record.beds,
        baths=record.baths,
        sqft=record.sqft,
        lot_sqft=record.lot_sqft,
        year_built=record.year_built,
        market_value_estimate=record.market_value_estimate,
        rent_estimate=record.rent_estimate,
        annual_taxes=record.annual_taxes,
        property_type=record.property_type,
        raw=record.raw,
        meta=meta,
    )


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_number(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _latest_numeric_key(obj: Dict[str, Any]) -> Optional[str]:
    numeric_keys = [key for key in obj.keys() if str(key).isdigit()]
    if not numeric_keys:
        return None
    return max(numeric_keys, key=int)
