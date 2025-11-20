"""Data provider abstraction and implementations for property ingestion."""

from .aggregation import DataAggregationService
from .hud_fmr import HudFmrProvider
from .marketplace import MarketplaceCompsProvider
from .models import (
    AreaIdentifier,
    AreaRentBenchmark,
    ProviderMetadata,
    ProviderResult,
    ProviderPriority,
    PropertyDataPatch,
)

__all__ = [
    "AreaIdentifier",
    "AreaRentBenchmark",
    "DataAggregationService",
    "HudFmrProvider",
    "MarketplaceCompsProvider",
    "ProviderMetadata",
    "ProviderPriority",
    "ProviderResult",
    "PropertyDataPatch",
]
