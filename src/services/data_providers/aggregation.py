from __future__ import annotations

import json
from typing import Iterable, List, Optional

from ...core.models import Address, ApiSource, PropertyData
from ...services.providers.base import PropertyDataProvider
from ...utils.logging import logger
from .adapters import LegacyProviderAdapter
from .base import BaseDataProvider
from .models import ProviderResult, ProviderPriority, record_source


class DataAggregationService:
    """Orchestrates provider calls and merges results into ``PropertyData``."""

    def __init__(
        self,
        *,
        primary_providers: Iterable[PropertyDataProvider] = (),
        open_data_providers: Iterable[BaseDataProvider] = (),
        marketplace_provider: Optional[BaseDataProvider] = None,
    ) -> None:
        self.primary_adapters: List[BaseDataProvider] = [
            LegacyProviderAdapter(provider, api_source)
            for provider, api_source in zip(
                primary_providers,
                self._resolve_sources(primary_providers),
            )
        ]
        self.open_data_providers = list(open_data_providers)
        self.marketplace_provider = marketplace_provider

    def aggregate(self, address: Address, *, existing: Optional[PropertyData] = None) -> PropertyData:
        aggregated = existing or PropertyData(address=address, meta={}, sources=[], provenance=[])

        for provider in self.primary_adapters:
            aggregated = self._apply_result(
                aggregated,
                provider.fetch_for_property(address),
                api_source=self._try_source_enum(provider.name),
                priority=ProviderPriority.PRIMARY,
            )

        for provider in self.open_data_providers:
            aggregated = self._apply_result(
                aggregated,
                provider.fetch_for_property(address) if hasattr(provider, "fetch_for_property") else None,
                priority=ProviderPriority.OPEN_DATA,
                api_source=self._try_source_enum(getattr(provider, "name", "")),
                prefer_existing=True,
            )

        if self.marketplace_provider:
            aggregated = self._apply_result(
                aggregated,
                self.marketplace_provider.fetch_for_property(address),
                api_source=ApiSource.MARKETPLACE,
                priority=ProviderPriority.MARKETPLACE,
                prefer_existing=True,
            )

        return aggregated

    @staticmethod
    def _try_source_enum(name: str) -> ApiSource | None:
        try:
            return ApiSource(name)
        except ValueError:
            return None

    def _apply_result(
        self,
        existing: PropertyData,
        provider_result: Optional[ProviderResult],
        *,
        api_source: ApiSource | None = None,
        priority: str = ProviderPriority.PRIMARY,
        prefer_existing: bool = False,
    ) -> PropertyData:
        if provider_result is None:
            return existing

        logger.info(
            "Merging provider result from %s (priority=%s)",
            provider_result.provider,
            priority,
        )

        updated = existing
        if provider_result.property_data:
            updated = provider_result.property_data.apply(existing, prefer_existing=prefer_existing)

        if provider_result.raw_payload is not None and provider_result.property_data:
            raw_key = provider_result.property_data.raw_reference or f"{provider_result.provider}_raw"
            try:
                updated.meta[raw_key] = json.dumps(provider_result.raw_payload)
            except TypeError:
                updated.meta[raw_key] = str(provider_result.raw_payload)

        effective_source = api_source or self._try_source_enum(provider_result.provider)
        updated = record_source(updated, provider_result, api_source=effective_source)

        if provider_result.area_rent_benchmarks:
            existing_benchmarks = []
            if "rent_benchmarks" in updated.meta:
                try:
                    existing_benchmarks = json.loads(updated.meta.get("rent_benchmarks", ""))
                except json.JSONDecodeError:
                    existing_benchmarks = []

            merged_benchmarks = existing_benchmarks + [
                {
                    "provider": provider_result.provider,
                    "bedroom_count": benchmark.bedroom_count,
                    "rent": benchmark.rent,
                    "currency": benchmark.currency,
                    "year": benchmark.year,
                    "area": benchmark.area.label(),
                }
                for benchmark in provider_result.area_rent_benchmarks
            ]

            updated.meta["rent_benchmarks"] = json.dumps(merged_benchmarks)

        return updated

    @staticmethod
    def _resolve_sources(providers: Iterable[PropertyDataProvider]) -> List[ApiSource]:
        mapping = {
            "ZillowProvider": ApiSource.ZILLOW,
            "RentometerProvider": ApiSource.RENTOMETER,
            "EstatedProvider": ApiSource.ESTATED,
            "RentcastProvider": ApiSource.RENTCAST,
            "RedfinProvider": ApiSource.REDFIN,
            "AttomProvider": ApiSource.ATTOM,
            "ClosingcorpProvider": ApiSource.CLOSINGCORP,
            "MockProvider": ApiSource.MOCK,
        }
        resolved: List[ApiSource] = []
        for provider in providers:
            resolved.append(mapping.get(provider.__class__.__name__, ApiSource.MOCK))
        return resolved
