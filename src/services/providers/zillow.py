from __future__ import annotations
from typing import Dict, Optional

import requests

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class ZillowProvider(PropertyDataProvider):
    """Zillow property data provider - requires API key configuration."""

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 10):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.bridgedataoutput.com/api/v2").rstrip("/")
        self.timeout = timeout
    
    def fetch(self, address: Address) -> Optional[PropertyData]:
        try:
            # Format address for Zillow API
            formatted_address = f"{address.line1}, {address.city}, {address.state} {address.zip}"
            
            # Search for property by address
            property_data = self._search_property(formatted_address)
            if not property_data:
                logger.info("ZillowProvider: no property found for %s", formatted_address)
                return None
            
            # Get detailed property information
            zpid = property_data.get('zpid')
            if not zpid:
                logger.info("ZillowProvider: search result missing ZPID for %s", formatted_address)
                return None

            detailed_data = self._get_property_details(zpid)
            if not detailed_data:
                return None
            
            # Map Zillow data to our PropertyData model
            meta: Dict[str, str] = {}
            for key in ('zpid', 'lastUpdated', 'zestimateConfidence'):
                value = detailed_data.get(key)
                if value is not None:
                    meta[key] = str(value)

            return PropertyData(
                address=address,
                beds=detailed_data.get('bedrooms'),
                baths=detailed_data.get('bathrooms'),
                sqft=detailed_data.get('finishedSqFt'),
                lot_sqft=detailed_data.get('lotSizeSqFt'),
                year_built=detailed_data.get('yearBuilt'),
                market_value_estimate=detailed_data.get('zestimate'),
                rent_estimate=detailed_data.get('rentZestimate'),
                annual_taxes=detailed_data.get('taxAssessment'),
                closing_cost_estimate=None,  # Zillow doesn't provide this
                meta=meta,
                sources=[ApiSource.ZILLOW]
            )
            
        except Exception as exc:
            logger.exception("Error fetching Zillow data for %s: %s", address, exc)
            return None
    
    def _search_property(self, address: str) -> Optional[dict]:
        """Search for property by address to get ZPID."""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'access_token': self.api_key,
                'address': address
            }
            
            response = requests.get(
                f"{self.base_url}/properties",
                headers=headers,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                props = data.get('properties') or []
                if props:
                    return props[0]
            else:
                logger.error(
                    "ZillowProvider: search failed with status %s and body %s",
                    response.status_code,
                    response.text,
                )

            return None
            
        except Exception as exc:
            logger.exception("Error searching property on Zillow: %s", exc)
            return None
    
    def _get_property_details(self, zpid: str) -> Optional[dict]:
        """Get detailed property information by ZPID."""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/properties/{zpid}",
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()

            logger.error(
                "ZillowProvider: detail fetch failed for %s with status %s and body %s",
                zpid,
                response.status_code,
                response.text,
            )
            return None
            
        except Exception as exc:
            logger.exception("Error getting Zillow property details for %s: %s", zpid, exc)
            return None 