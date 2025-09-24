from __future__ import annotations
from typing import Optional, List
from core.models import Address, PropertyData
from .providers.mock import MockProvider
#from .providers.zillow import ZillowProvider
# from .providers.rentometer import RentometerProvider  # TODO
# from .providers.attom import AttomProvider  # TODO
# from .providers.closingcorp import ClosingcorpProvider  # TODO
#from utils.config import settings

def merge(a: PropertyData, b: PropertyData) -> PropertyData:
    """Prefer non-null values; combine sources/meta."""
    # TODO: implement safe merge
    return a

def fetch_property(address: Address, use_mock_if_empty: bool = True) -> Optional[PropertyData]:
    providers: List = []
    
    # Add Zillow provider if API key is configured
    #if settings.ZILLOW_API_KEY:
    #if 0!=0:
        #providers.append(ZillowProvider(settings.ZILLOW_API_KEY))
    
    # TODO: append other real providers if API keys present
    # if settings.RENTOMETER_API_KEY:
    #     providers.append(RentometerProvider(settings.RENTOMETER_API_KEY))
    # if settings.ATTOM_API_KEY:
    #     providers.append(AttomProvider(settings.ATTOM_API_KEY))
    # if settings.CLOSINGCORP_API_KEY:
    #     providers.append(ClosingcorpProvider(settings.CLOSINGCORP_API_KEY))
    
    if not providers and use_mock_if_empty:
        providers = [MockProvider()]

    merged: Optional[PropertyData] = None
    for p in providers:
        data = p.fetch(address)
        if not data: continue
        merged = data if merged is None else merge(merged, data)
    return merged 