from __future__ import annotations
from typing import Optional

from ...core.models import Address, ApiSource, PropertyData
from .base import PropertyDataProvider


class MockProvider(PropertyDataProvider):
    def fetch(self, address: Address) -> Optional[PropertyData]:
        # Placeholder, deterministic values for repeatability
        return PropertyData(
            address=address,
            beds=3, baths=2, sqft=1600, lot_sqft=6000, year_built=1995,
            market_value_estimate=375_000, rent_estimate=2_450,
            annual_taxes=4_200, closing_cost_estimate=8_000,
            meta={}, sources=[ApiSource.MOCK],
        ) 