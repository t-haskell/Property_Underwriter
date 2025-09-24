from __future__ import annotations
from typing import Optional
from ...core.models import Address, PropertyData, ApiSource
from .base import PropertyDataProvider

class AttomProvider(PropertyDataProvider):
    """ATTOM property and tax data provider - requires API key configuration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch(self, address: Address) -> Optional[PropertyData]:
        # TODO: Implement ATTOM API integration
        # - Property details and characteristics
        # - Tax history and assessments
        # - Lot and structure attributes
        return None 