from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional
import requests
import time

from ..core.models import Address
from ..utils.logging import logger

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"


class NominatimError(RuntimeError):
    pass


def _is_enabled() -> bool:
    """Nominatim is always enabled as it's free."""
    return True


def get_place_suggestions(query: str, country: Optional[str] = "us", limit: int = 5) -> List[Dict[str, str]]:
    """
    Get address suggestions from OpenStreetMap Nominatim.
    Completely free, no API key required.
    """
    logger.info(f"Getting place suggestions for {query}")
    if not query.strip():
        return []

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
        "countrycodes": country.lower() if country else None,
        "dedupe": 1,  # Remove duplicates
    }

    try:
        # Add a small delay to be respectful to the free service
        time.sleep(0.1)
        prepared_request = requests.Request('GET', f"{NOMINATIM_BASE_URL}/search", params=params).prepare()
        logger.debug("Nominatim request URL: %s", prepared_request.url)
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params=params,
            timeout=10,
            headers={"User-Agent": "PropertyUnderwriter/1.0"}  # Required by Nominatim
        )
        response.raise_for_status()
        
        results = response.json()
        
        suggestions = []
        for result in results:
            if result.get("display_name"):
                suggestions.append({
                    "description": result["display_name"],
                    "place_id": result.get("place_id", ""),
                    "lat": result.get("lat", ""),
                    "lon": result.get("lon", "")
                })
        
        return suggestions
        
    except Exception as exc:
        logger.exception("Nominatim autocomplete failed: %s", exc)
        return []


@lru_cache(maxsize=256)
def get_place_details(place_id: str) -> Optional[Address]:
    """
    Get detailed address information from Nominatim.
    Note: Nominatim doesn't use place_id the same way as Google Places,
    so this function extracts address from the cached suggestion.
    """
    try:
        # For Nominatim, we'll use reverse geocoding with lat/lon
        # This is a simplified implementation - in practice, you'd store
        # the lat/lon from the suggestion and use reverse geocoding
        return None  # Placeholder - would need lat/lon for reverse geocoding
        
    except Exception as exc:
        logger.exception("Nominatim details lookup failed: %s", exc)
        return None


def get_address_from_suggestion(suggestion: Dict[str, str]) -> Optional[Address]:
    """
    Parse a Nominatim suggestion into an Address object.
    Nominatim format: "123, Main Street, Charlestown, Boston, Suffolk County, Massachusetts, 02129, United States"
    """
    try:
        description = suggestion.get("description", "")
        if not description:
            return None
            
        # Split by comma and clean up
        parts = [part.strip() for part in description.split(",")]
        
        if len(parts) < 4:
            return None
            
        import re
        
        # Extract components
        line1 = parts[0].strip()
        
        # State abbreviations and full names mapping
        state_mapping = {
            'AL': 'AL', 'Alabama': 'AL',
            'AK': 'AK', 'Alaska': 'AK',
            'AZ': 'AZ', 'Arizona': 'AZ',
            'AR': 'AR', 'Arkansas': 'AR',
            'CA': 'CA', 'California': 'CA',
            'CO': 'CO', 'Colorado': 'CO',
            'CT': 'CT', 'Connecticut': 'CT',
            'DE': 'DE', 'Delaware': 'DE',
            'FL': 'FL', 'Florida': 'FL',
            'GA': 'GA', 'Georgia': 'GA',
            'HI': 'HI', 'Hawaii': 'HI',
            'ID': 'ID', 'Idaho': 'ID',
            'IL': 'IL', 'Illinois': 'IL',
            'IN': 'IN', 'Indiana': 'IN',
            'IA': 'IA', 'Iowa': 'IA',
            'KS': 'KS', 'Kansas': 'KS',
            'KY': 'KY', 'Kentucky': 'KY',
            'LA': 'LA', 'Louisiana': 'LA',
            'ME': 'ME', 'Maine': 'ME',
            'MD': 'MD', 'Maryland': 'MD',
            'MA': 'MA', 'Massachusetts': 'MA',
            'MI': 'MI', 'Michigan': 'MI',
            'MN': 'MN', 'Minnesota': 'MN',
            'MS': 'MS', 'Mississippi': 'MS',
            'MO': 'MO', 'Missouri': 'MO',
            'MT': 'MT', 'Montana': 'MT',
            'NE': 'NE', 'Nebraska': 'NE',
            'NV': 'NV', 'Nevada': 'NV',
            'NH': 'NH', 'New Hampshire': 'NH',
            'NJ': 'NJ', 'New Jersey': 'NJ',
            'NM': 'NM', 'New Mexico': 'NM',
            'NY': 'NY', 'New York': 'NY',
            'NC': 'NC', 'North Carolina': 'NC',
            'ND': 'ND', 'North Dakota': 'ND',
            'OH': 'OH', 'Ohio': 'OH',
            'OK': 'OK', 'Oklahoma': 'OK',
            'OR': 'OR', 'Oregon': 'OR',
            'PA': 'PA', 'Pennsylvania': 'PA',
            'RI': 'RI', 'Rhode Island': 'RI',
            'SC': 'SC', 'South Carolina': 'SC',
            'SD': 'SD', 'South Dakota': 'SD',
            'TN': 'TN', 'Tennessee': 'TN',
            'TX': 'TX', 'Texas': 'TX',
            'UT': 'UT', 'Utah': 'UT',
            'VT': 'VT', 'Vermont': 'VT',
            'VA': 'VA', 'Virginia': 'VA',
            'WA': 'WA', 'Washington': 'WA',
            'WV': 'WV', 'West Virginia': 'WV',
            'WI': 'WI', 'Wisconsin': 'WI',
            'WY': 'WY', 'Wyoming': 'WY'
        }
        
        city = ""
        state = ""
        zip_code = ""
        
        # Find ZIP code (5 digits)
        for part in parts:
            zip_match = re.search(r'\d{5}(-\d{4})?', part)
            if zip_match:
                zip_code = zip_match.group()
                break
        
        # Find state
        for part in parts:
            if part in state_mapping:
                state = state_mapping[part]
                break
        
        # Find city - look for the most likely city name
        if state:
            # Find the index of the state
            state_index = -1
            for i, part in enumerate(parts):
                if part in state_mapping:
                    state_index = i
                    break
            
            # Look backwards from state for city, skipping counties
            for i in range(state_index - 1, 0, -1):
                potential_city = parts[i].strip()
                # Skip counties and other administrative areas
                if not any(word in potential_city.lower() for word in ['county', 'parish', 'borough', 'township']) and potential_city not in state_mapping:
                    city = potential_city
                    break
        
        # If we still don't have city, try the 2nd or 3rd part
        if not city and len(parts) >= 3:
            # Skip street number and street name
            for i in range(1, min(4, len(parts))):
                potential_city = parts[i].strip()
                # Skip if it looks like a county or state
                if not any(word in potential_city.lower() for word in ['county', 'parish', 'borough', 'township', 'state']) and potential_city not in state_mapping:
                    city = potential_city
                    break
        
        if line1 and city and state:
            return Address(line1=line1, city=city, state=state, zip=zip_code)
            
    except Exception as exc:
        logger.exception("Failed to parse Nominatim suggestion: %s", exc)
        
    return None
