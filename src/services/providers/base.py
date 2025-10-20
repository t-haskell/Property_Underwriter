from __future__ import annotations

from typing import Optional

from ...core.models import Address, PropertyData
from ...utils.scaffolding import scaffold

class PropertyDataProvider:
    """Interface all providers implement."""

    def fetch(self, address: Address) -> Optional[PropertyData]:
        scaffold("PropertyDataProvider.fetch")
        return PropertyData(address=Address(line1="", city="", state="", zip=""), beds=None, baths=None, sqft=None, lot_sqft=None, year_built=None, market_value_estimate=None,  rent_estimate=None, annual_taxes=None, closing_cost_estimate=None, meta={"":""}, sources=[])
