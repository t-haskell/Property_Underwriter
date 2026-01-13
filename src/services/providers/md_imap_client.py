from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import httpx

from ...core.models import Address
from ..property_merging import NormalizedPropertyRecord, ProviderName
from ...utils.logging import logger
from .config import md_imap


@dataclass(slots=True)
class RawMdImapRecord:
    attributes: Dict[str, Any]
    geometry: Dict[str, Any] | None = None


@dataclass(slots=True)
class MdImapProperty:
    address: Address
    owner_name: Optional[str] = None
    assessed_land_value: Optional[float] = None
    assessed_building_value: Optional[float] = None
    land_use_code: Optional[str] = None
    property_type: Optional[str] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    annual_taxes: Optional[float] = None
    geometry: Dict[str, Any] | None = None
    raw: RawMdImapRecord | None = None


class MdImapClient:
    """Typed client for the MD iMAP Parcel Points ArcGIS layer."""

    def __init__(self, base_url: str, layer_id: str, timeout: int = md_imap.DEFAULT_TIMEOUT_SEC) -> None:
        self.base_url = base_url.rstrip("/")
        self.layer_id = layer_id
        self.timeout = timeout

    def _build_query(self, address: Address) -> Dict[str, str]:
        return {
            "where": f"{md_imap.FIELD_MAPPINGS['zip']}='{address.zip}'",
            "outFields": "*",
            "f": "json",
        }

    def _endpoint(self) -> str:
        return f"{self.base_url}/{self.layer_id}/query"

    def get_by_address(self, address: Address) -> Optional[MdImapProperty]:
        if not self.base_url or not self.layer_id:
            logger.info("MD iMAP client not configured; skipping fetch")
            return None

        params = self._build_query(address)
        try:
            response = httpx.get(self._endpoint(), params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            logger.warning("MD iMAP request failed: %s", exc)
            return None

        payload = response.json()
        features = payload.get("features") or []
        if not isinstance(features, list) or not features:
            return None

        raw_record = RawMdImapRecord(
            attributes=features[0].get("attributes", {}),
            geometry=features[0].get("geometry"),
        )
        return self._map_record(raw_record)

    def _map_record(self, record: RawMdImapRecord) -> MdImapProperty:
        attrs = record.attributes
        address = Address(
            line1=str(attrs.get(md_imap.FIELD_MAPPINGS.get("address", ""), "")),
            city=str(attrs.get(md_imap.FIELD_MAPPINGS.get("city", ""), "")),
            state=str(attrs.get(md_imap.FIELD_MAPPINGS.get("state", "MD"), "MD")),
            zip=str(attrs.get(md_imap.FIELD_MAPPINGS.get("zip", ""), "")),
        )
        return MdImapProperty(
            address=address,
            owner_name=attrs.get(md_imap.FIELD_MAPPINGS.get("owner_name", "")),
            assessed_land_value=_safe_number(
                attrs.get(md_imap.FIELD_MAPPINGS.get("assessed_land", ""))
            ),
            assessed_building_value=_safe_number(
                attrs.get(md_imap.FIELD_MAPPINGS.get("assessed_building", ""))
            ),
            land_use_code=_safe_str(attrs.get(md_imap.FIELD_MAPPINGS.get("land_use_code", ""))),
            property_type=_safe_str(attrs.get(md_imap.FIELD_MAPPINGS.get("property_type", ""))),
            lot_sqft=_safe_int(attrs.get(md_imap.FIELD_MAPPINGS.get("lot_sqft", ""))),
            year_built=_safe_int(attrs.get(md_imap.FIELD_MAPPINGS.get("year_built", ""))),
            annual_taxes=_safe_number(attrs.get(md_imap.FIELD_MAPPINGS.get("taxes", ""))),
            geometry=record.geometry,
            raw=record,
        )


def normalize_md_imap(record: MdImapProperty) -> NormalizedPropertyRecord:
    meta: Dict[str, str] = {}
    if record.land_use_code:
        meta["landUseCode"] = record.land_use_code
    if record.property_type:
        meta["propertyType"] = record.property_type
    if record.owner_name:
        meta["ownerName"] = record.owner_name

    if record.land_use_code in md_imap.MULTIFAMILY_LAND_USE_CODES:
        meta["isMultiFamily"] = "true"

    return NormalizedPropertyRecord(
        provider=ProviderName.MD_IMAP,
        fetched_at=datetime.now(UTC),
        address=record.address,
        beds=None,
        baths=None,
        sqft=None,
        lot_sqft=record.lot_sqft,
        year_built=record.year_built,
        market_value_estimate=None,
        rent_estimate=None,
        annual_taxes=record.annual_taxes,
        owner_name=record.owner_name,
        land_use_code=record.land_use_code,
        property_type=record.property_type,
        geometry=record.geometry,
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
