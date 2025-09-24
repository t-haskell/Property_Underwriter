from __future__ import annotations
from typing import Optional
import requests
from ...core.models import Address, PropertyData, ApiSource
from .base import PropertyDataProvider

class ZillowProvider(PropertyDataProvider):
    """Zillow property data provider - requires API key configuration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bridgedataoutput.com/api/v2"
    
    def fetch(self, address: Address) -> Optional[PropertyData]:
        try:
            # Format address for Zillow API
            formatted_address = f"{address.line1}, {address.city}, {address.state} {address.zip}"
            
            # Search for property by address
            property_data = self._search_property(formatted_address)
            if not property_data:
                return None
            
            # Get detailed property information
            detailed_data = self._get_property_details(property_data.get('zpid'))
            if not detailed_data:
                return None
            
            # Map Zillow data to our PropertyData model
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
                meta={
                    'zpid': detailed_data.get('zpid'),
                    'last_updated': detailed_data.get('lastUpdated'),
                    'confidence': detailed_data.get('zestimateConfidence')
                },
                sources=[ApiSource.ZILLOW]
            )
            
        except Exception as e:
            print(f"Error fetching Zillow data: {e}")
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
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('properties') and len(data['properties']) > 0:
                    return data['properties'][0]
            
            return None
            
        except Exception as e:
            print(f"Error searching property: {e}")
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
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"Error getting property details: {e}")
            return None 