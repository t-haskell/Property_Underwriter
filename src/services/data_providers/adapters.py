from __future__ import annotations

from typing import Optional

from ...core.models import Address, ApiSource
from ...services.providers.base import PropertyDataProvider
from ...utils.logging import logger
from .base import BaseDataProvider
from .models import ProviderMetadata, ProviderResult, PropertyDataPatch


class LegacyProviderAdapter(BaseDataProvider):
    """Wrap existing ``PropertyDataProvider`` implementations to the new contract."""

    def __init__(self, provider: PropertyDataProvider, api_source: ApiSource) -> None:
        self.provider = provider
        self.api_source = api_source
        self.name = api_source.value

    def fetch_for_property(self, address: Address) -> Optional[ProviderResult]:
        try:
            result = self.provider.fetch(address)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Legacy provider %s failed: %s", self.provider, exc)
            return None

        if result is None:
            return None

        if result.sources:
            self.api_source = result.sources[0]
            self.name = self.api_source.value

        patch = PropertyDataPatch.from_property_data(
            result, raw_reference=f"{self.name}_raw"
        )
        return ProviderResult(
            metadata=ProviderMetadata(provider_name=self.name),
            property_data=patch,
            raw_payload=(
                result.meta.get(patch.raw_reference)
                if result.meta and patch.raw_reference
                else None
            ),
        )
