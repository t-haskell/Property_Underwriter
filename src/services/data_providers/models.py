from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from ...core.models import ApiSource, PropertyData, SourceAttribution


@dataclass(slots=True)
class AreaIdentifier:
    zip: str | None = None
    county: str | None = None
    state: str | None = None
    metro: str | None = None

    def label(self) -> str:
        if self.metro:
            return self.metro
        if self.county and self.state:
            return f"{self.county}, {self.state}"
        if self.zip:
            return self.zip
        return "unknown"


@dataclass(slots=True)
class AreaRentBenchmark:
    area: AreaIdentifier
    bedroom_count: Optional[int]
    rent: float
    currency: str = "USD"
    year: Optional[int] = None


@dataclass(slots=True)
class PropertyDataPatch:
    """A partial update to ``PropertyData`` from a provider."""

    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    market_value_estimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    annual_taxes: Optional[float] = None
    closing_cost_estimate: Optional[float] = None
    meta: Dict[str, str] = field(default_factory=dict)
    fields: List[str] = field(default_factory=list)
    raw_reference: Optional[str] = None

    def apply(self, existing: PropertyData, *, prefer_existing: bool = False) -> PropertyData:
        def choose(new, old):
            if prefer_existing and old is not None:
                return old
            return new if new is not None else old

        merged_meta = {**existing.meta, **{k: v for k, v in self.meta.items() if v is not None}}

        return PropertyData(
            address=existing.address,
            beds=choose(self.beds, existing.beds),
            baths=choose(self.baths, existing.baths),
            sqft=choose(self.sqft, existing.sqft),
            lot_sqft=choose(self.lot_sqft, existing.lot_sqft),
            year_built=choose(self.year_built, existing.year_built),
            market_value_estimate=choose(
                self.market_value_estimate, existing.market_value_estimate
            ),
            rent_estimate=choose(self.rent_estimate, existing.rent_estimate),
            annual_taxes=choose(self.annual_taxes, existing.annual_taxes),
            closing_cost_estimate=choose(
                self.closing_cost_estimate, existing.closing_cost_estimate
            ),
            meta=merged_meta,
            sources=list(existing.sources),
            provenance=list(existing.provenance),
        )

    @classmethod
    def from_property_data(
        cls, data: PropertyData, *, raw_reference: Optional[str] = None
    ) -> "PropertyDataPatch":
        fields = [
            name
            for name in (
                "beds",
                "baths",
                "sqft",
                "lot_sqft",
                "year_built",
                "market_value_estimate",
                "rent_estimate",
                "annual_taxes",
                "closing_cost_estimate",
            )
            if getattr(data, name) is not None
        ]
        return cls(
            beds=data.beds,
            baths=data.baths,
            sqft=data.sqft,
            lot_sqft=data.lot_sqft,
            year_built=data.year_built,
            market_value_estimate=data.market_value_estimate,
            rent_estimate=data.rent_estimate,
            annual_taxes=data.annual_taxes,
            closing_cost_estimate=data.closing_cost_estimate,
            meta=dict(data.meta),
            fields=fields,
            raw_reference=raw_reference,
        )


@dataclass(slots=True)
class ProviderMetadata:
    provider_name: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    request_id: Optional[str] = None


@dataclass(slots=True)
class ProviderResult:
    metadata: ProviderMetadata
    property_data: Optional[PropertyDataPatch] = None
    area_rent_benchmarks: List[AreaRentBenchmark] = field(default_factory=list)
    raw_payload: Any | None = None
    errors: List[str] = field(default_factory=list)

    def provenance(self) -> List[SourceAttribution]:
        if not self.property_data or not self.property_data.fields:
            return []
        return [
            SourceAttribution(
                provider=self.metadata.provider_name,
                fields=list(self.property_data.fields),
                fetched_at=self.metadata.fetched_at,
                request_id=self.metadata.request_id,
                raw_reference=self.property_data.raw_reference,
            )
        ]

    @property
    def provider(self) -> str:
        return self.metadata.provider_name


class ProviderPriority:
    PRIMARY = "primary"
    OPEN_DATA = "open_data"
    MARKETPLACE = "marketplace"
    FALLBACK = "fallback"


def record_source(
    property_data: PropertyData,
    provider_result: ProviderResult,
    *,
    api_source: ApiSource | None = None,
) -> PropertyData:
    """Attach source enums and provenance to a property snapshot."""

    sources = list(property_data.sources)
    if api_source and api_source not in sources:
        sources.append(api_source)

    provenance = list(property_data.provenance)
    provenance.extend(provider_result.provenance())

    return PropertyData(
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
        meta=dict(property_data.meta),
        sources=sources,
        provenance=provenance,
    )
