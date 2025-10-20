from __future__ import annotations

from typing import Optional

from ...core.models import Address, PropertyData
from ...utils.scaffolding import scaffold


class PropertyDataProvider:
    """Interface all providers implement."""

    def fetch(self, address: Address) -> Optional[PropertyData]:
        scaffold("PropertyDataProvider.fetch")
