from __future__ import annotations
from typing import Optional
from ...core.models import Address, PropertyData

class PropertyDataProvider:
    """Interface all providers implement."""
    def fetch(self, address: Address) -> Optional[PropertyData]:
        raise NotImplementedError 