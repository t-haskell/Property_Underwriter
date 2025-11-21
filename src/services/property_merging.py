from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Dict, Iterable, List, Optional

from ..core.models import Address, ApiSource, PropertyData


class ProviderName:
    MD_IMAP = "MD_IMAP"
    MASS_GIS = "MASS_GIS"
    RENTCAST = "RENTCAST"
    ESTATED = "ESTATED"
    LEGACY = "LEGACY"
    CACHED = "CACHED"


@dataclass(slots=True)
class NormalizedPropertyRecord:
    provider: str
    fetched_at: datetime
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
    land_use_code: Optional[str] = None
    property_type: Optional[str] = None
    closing_cost_estimate: Optional[float] = None
    geometry: Optional[dict] = None
    raw: object | None = None
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class FieldSourceInfo:
    field: str
    provider: str
    reason: str


@dataclass(slots=True)
class MergedPropertyResult:
    property: PropertyData
    field_sources: List[FieldSourceInfo]
    all_raw_records: List[NormalizedPropertyRecord]


class ProviderCache:
    """Simple in-memory cache to avoid hammering commercial APIs."""

    def __init__(self, ttl_minutes: int) -> None:
        self.ttl = timedelta(minutes=ttl_minutes)
        self._store: Dict[str, tuple[datetime, NormalizedPropertyRecord]] = {}

    def get(self, key: str) -> Optional[NormalizedPropertyRecord]:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, record = entry
        if datetime.now(UTC) > expires_at:
            self._store.pop(key, None)
            return None
        return record

    def set(self, key: str, record: NormalizedPropertyRecord) -> None:
        self._store[key] = (datetime.now(UTC) + self.ttl, record)


def _pick_value(
    field: str,
    records: Iterable[NormalizedPropertyRecord],
    priority: List[str],
    reason_lookup: Dict[str, str],
    field_sources: List[FieldSourceInfo],
):
    for provider in priority:
        for record in records:
            if record.provider != provider:
                continue
            value = getattr(record, field)
            if value is None:
                continue
            field_sources.append(
                FieldSourceInfo(
                    field=field,
                    provider=provider,
                    reason=reason_lookup.get(provider, "prioritized provider"),
                )
            )
            return value, provider
    return None, None


def merge_property_records(records: List[NormalizedPropertyRecord]) -> MergedPropertyResult:
    """Merge normalized provider records into a single ``PropertyData`` snapshot."""

    if not records:
        raise ValueError("merge_property_records requires at least one record")

    field_sources: List[FieldSourceInfo] = []
    assessor_priority = [
        ProviderName.MD_IMAP,
        ProviderName.MASS_GIS,
        ProviderName.ESTATED,
        ProviderName.RENTCAST,
        ProviderName.LEGACY,
        ProviderName.CACHED,
    ]
    valuation_priority = [
        ProviderName.RENTCAST,
        ProviderName.ESTATED,
        ProviderName.MD_IMAP,
        ProviderName.MASS_GIS,
        ProviderName.LEGACY,
        ProviderName.CACHED,
    ]

    reasons = {
        ProviderName.MD_IMAP: "official assessor (MD)",
        ProviderName.MASS_GIS: "official assessor (MA)",
        ProviderName.RENTCAST: "live valuation / rent API",
        ProviderName.ESTATED: "nationwide enrichment",
        ProviderName.LEGACY: "legacy aggregated provider",
        ProviderName.CACHED: "cached snapshot",
    }

    canonical_address = records[0].address

    beds, beds_source = _pick_value("beds", records, assessor_priority, reasons, field_sources)
    baths, baths_source = _pick_value("baths", records, assessor_priority, reasons, field_sources)
    sqft, sqft_source = _pick_value("sqft", records, assessor_priority, reasons, field_sources)
    lot_sqft, lot_sqft_source = _pick_value("lot_sqft", records, assessor_priority, reasons, field_sources)
    year_built, year_built_source = _pick_value("year_built", records, assessor_priority, reasons, field_sources)

    market_value, market_source = _pick_value(
        "market_value_estimate", records, valuation_priority, reasons, field_sources
    )
    rent_estimate, rent_source = _pick_value(
        "rent_estimate", records, valuation_priority, reasons, field_sources
    )
    annual_taxes, taxes_source = _pick_value(
        "annual_taxes", records, assessor_priority, reasons, field_sources
    )
    closing_cost, closing_source = _pick_value(
        "closing_cost_estimate", records, valuation_priority, reasons, field_sources
    )

    meta: Dict[str, str] = {}
    for record in records:
        for key, value in record.meta.items():
            meta.setdefault(key, value)
    chosen_sources = {
        "beds": beds_source,
        "baths": baths_source,
        "sqft": sqft_source,
        "lot_sqft": lot_sqft_source,
        "year_built": year_built_source,
        "market_value_estimate": market_source,
        "rent_estimate": rent_source,
        "annual_taxes": taxes_source,
        "closing_cost_estimate": closing_source,
    }
    for field, provider in chosen_sources.items():
        if provider:
            meta[f"{field}.source"] = provider

    meta["dataSources"] = ",".join(sorted({record.provider for record in records}))

    land_use, land_use_source = _pick_value(
        "land_use_code", records, assessor_priority, reasons, field_sources
    )
    property_type, property_type_source = _pick_value(
        "property_type", records, assessor_priority, reasons, field_sources
    )
    owner_name, owner_source = _pick_value(
        "owner_name", records, assessor_priority, reasons, field_sources
    )

    for field, provider in (
        ("land_use_code", land_use_source),
        ("property_type", property_type_source),
        ("owner_name", owner_source),
    ):
        if provider:
            meta[f"{field}.source"] = provider

    geometry_source = None
    geometry = None
    for provider in assessor_priority:
        for record in records:
            if record.provider == provider and record.geometry is not None:
                geometry = record.geometry
                geometry_source = provider
                break
        if geometry is not None:
            break

    if geometry_source:
        meta["geometry.source"] = geometry_source

    sources: List[ApiSource] = []
    provider_to_api_source = {
        ProviderName.MD_IMAP: ApiSource.MD_IMAP,
        ProviderName.MASS_GIS: ApiSource.MASS_GIS,
        ProviderName.RENTCAST: ApiSource.RENTCAST,
        ProviderName.ESTATED: ApiSource.ESTATED,
        ProviderName.LEGACY: ApiSource.MOCK,
        ProviderName.CACHED: ApiSource.MOCK,
    }
    for record in records:
        api_source = provider_to_api_source.get(record.provider)
        if api_source and api_source not in sources:
            sources.append(api_source)

    property_data = PropertyData(
        address=canonical_address,
        beds=beds,
        baths=baths,
        sqft=sqft,
        lot_sqft=lot_sqft,
        year_built=year_built,
        market_value_estimate=market_value,
        rent_estimate=rent_estimate,
        annual_taxes=annual_taxes,
        closing_cost_estimate=closing_cost,
        meta=meta,
        sources=sources,
    )

    return MergedPropertyResult(
        property=property_data,
        field_sources=field_sources,
        all_raw_records=records,
    )


def cached_record_key(provider: str, address: Address) -> str:
    return f"{provider}:{address.line1}|{address.city}|{address.state}|{address.zip}"


def normalize_property_data(
    provider: str, property_data: PropertyData, raw: object | None = None
) -> NormalizedPropertyRecord:
    return NormalizedPropertyRecord(
        provider=provider,
        fetched_at=datetime.now(UTC),
        address=property_data.address,
        beds=property_data.beds,
        baths=property_data.baths,
        sqft=property_data.sqft,
        lot_sqft=property_data.lot_sqft,
        year_built=property_data.year_built,
        market_value_estimate=property_data.market_value_estimate,
        rent_estimate=property_data.rent_estimate,
        annual_taxes=property_data.annual_taxes,
        closing_cost_estimate=property_data.closing_cost_estimate,
        raw=raw,
        meta=dict(property_data.meta),
    )
