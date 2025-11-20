from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ...core.models import Address
from .models import ProviderResult


class BaseDataProvider(ABC):
    """Base interface for all data providers used in the ingestion layer."""

    name: str

    @abstractmethod
    def fetch_for_property(self, address: Address) -> Optional[ProviderResult]:
        """Fetch data scoped to a specific property/address."""

    def fetch_for_area(self, area_identifier) -> Optional[ProviderResult]:  # noqa: ANN001
        """Fetch data scoped to an area (zip/county/metro). Optional."""
        return None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.__class__.__name__}(name={getattr(self, 'name', '<unknown>')})"
