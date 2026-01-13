from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import httpx

from ...core.models import Address
from ..property_merging import NormalizedPropertyRecord, ProviderName
from ...utils.logging import logger
from .config import estated


@dataclass(slots=True)
class EstatedProperty:
    address: Address
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    market_value_estimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    annual_taxes: Optional[float] = None
    owner_name: Optional[str] = None
    property_type: Optional[str] = None
    raw: Dict[str, Any] | None = None


class EstatedClient:
    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = estated.DEFAULT_TIMEOUT_SEC) -> None:
        self.api_key = api_key
        self.base_url = (base_url or estated.BASE_URL).rstrip("/")
        self.timeout = timeout

    def get_by_address(self, address: Address) -> Optional[EstatedProperty]:
        params = {"token": self.api_key, "address": f"{address.line1}, {address.city}, {address.state} {address.zip}"}
        try:
            response = httpx.get(
                f"{self.base_url}{estated.PROPERTY_ENDPOINT}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            logger.warning("Estated request failed: %s", exc)
            return None

        payload = response.json() or {}
        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        return self._map_record(data)

    def _map_record(self, payload: Dict[str, Any]) -> EstatedProperty:
        def _pluck(mapping_key: str) -> Any:
            parts = mapping_key.split(".")
            current: Any = payload
            for part in parts:
                if not isinstance(current, dict):
                    return None
                current = current.get(part)
            return current

        return EstatedProperty(
            address=Address(
                line1=str(payload.get("mailing_address", {}).get("line1", "")),
                city=str(payload.get("mailing_address", {}).get("city", "")),
                state=str(payload.get("mailing_address", {}).get("state", "")),
                zip=str(payload.get("mailing_address", {}).get("zip", "")),
            ),
            beds=_safe_number(_pluck(estated.FIELD_MAPPINGS.get("beds", ""))),
            baths=_safe_number(_pluck(estated.FIELD_MAPPINGS.get("baths", ""))),
            sqft=_safe_int(_pluck(estated.FIELD_MAPPINGS.get("sqft", ""))),
            lot_sqft=_safe_int(_pluck(estated.FIELD_MAPPINGS.get("lot_sqft", ""))),
            year_built=_safe_int(_pluck(estated.FIELD_MAPPINGS.get("year_built", ""))),
            market_value_estimate=_safe_number(_pluck(estated.FIELD_MAPPINGS.get("market_value_estimate", ""))),
            rent_estimate=_safe_number(_pluck(estated.FIELD_MAPPINGS.get("rent_estimate", ""))),
            annual_taxes=_safe_number(_pluck(estated.FIELD_MAPPINGS.get("annual_taxes", ""))),
            owner_name=_safe_str(_pluck(estated.FIELD_MAPPINGS.get("owner_name", ""))),
            property_type=_safe_str(_pluck(estated.FIELD_MAPPINGS.get("property_type", ""))),
            raw=payload,
        )


def normalize_estated(record: EstatedProperty) -> NormalizedPropertyRecord:
    meta: Dict[str, str] = {}
    if record.property_type:
        meta["propertyType"] = record.property_type
    if record.owner_name:
        meta["ownerName"] = record.owner_name

    return NormalizedPropertyRecord(
        provider=ProviderName.ESTATED,
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
        owner_name=record.owner_name,
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
