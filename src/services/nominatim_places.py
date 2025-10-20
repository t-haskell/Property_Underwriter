from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional
import requests
import time

from ..core.models import Address
from ..utils.logging import logger

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

# Normalization map for state values returned by Nominatim.
# The keys are intentionally mixed case to support both abbreviations and full names.
STATE_NAME_TO_CODE: Dict[str, str] = {
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


class NominatimError(RuntimeError):
    pass


def _is_enabled() -> bool:
    """Nominatim is always enabled as it's free."""
    return True


def _normalize_state(state_value: Optional[str]) -> str:
    """Return the two-letter state code for the provided value."""
    if not state_value:
        return ""
    state_value = state_value.strip()
    if not state_value:
        return ""
    # Prefer the two-letter code if we already have one.
    if len(state_value) == 2 and state_value.upper() in STATE_NAME_TO_CODE.values():
        return state_value.upper()
    normalized = STATE_NAME_TO_CODE.get(state_value)
    if normalized:
        return normalized
    return STATE_NAME_TO_CODE.get(state_value.title(), "")


def _extract_city(address: Dict[str, str]) -> str:
    """Best-effort retrieval of the city/locality from a Nominatim address payload."""
    # Nominatim may return a city in different keys depending on the locality size.
    city_candidates = [
        "city",
        "town",
        "village",
        "municipality",
        "hamlet",
        "suburb",
        "neighbourhood",
    ]
    for key in city_candidates:
        value = address.get(key)
        if value:
            return value
    return ""


def _extract_street_line(address: Dict[str, str]) -> str:
    """Construct the street line (house number + street name) when available."""
    street_candidates = [
        "road",
        "residential",
        "pedestrian",
        "footway",
        "street",
        "path",
        "cycleway",
        "construction",
    ]
    street = ""
    for key in street_candidates:
        value = address.get(key)
        if value:
            street = value
            break

    house_number = address.get("house_number") or ""
    # Some locations only have a name (e.g., "Empire State Building")
    if not street:
        building = address.get("building")
        if isinstance(building, str):
            street = building

    components = [component for component in [house_number, street] if component]
    return " ".join(components)


def _format_description(street: str, city: str, state: str, postal_code: str, fallback: str) -> str:
    """Generate a human-readable suggestion description."""
    parts = [street, city, " ".join(val for val in [state, postal_code] if val).strip()]
    formatted = ", ".join(part for part in parts if part)
    return formatted or fallback


def _is_full_address(street: str, city: str, state: str, postal_code: str) -> bool:
    """Return True if the components represent a full street address.

    Criteria:
    - All components present: street, city, state (2-letter), postal_code
    - Street likely contains a house number (simple digit check)
    """
    if not (street and city and state and postal_code):
        return False
    has_number = any(ch.isdigit() for ch in street)
    return has_number


def get_place_suggestions(query: str, country: Optional[str] = "us", limit: int = 5) -> List[Dict[str, str]]:
    """Fetch structured address suggestions (street, city, state, ZIP) from Nominatim."""
    trimmed_query = query.strip()
    if not trimmed_query:
        logger.debug("Skipping Nominatim lookup for blank query")
        return []

    params: Dict[str, str] = {
        "q": trimmed_query,
        "format": "json",
        "addressdetails": "1",
        "limit": str(max(limit, 1)),
        "dedupe": "1",
    }
    if country:
        params["countrycodes"] = country.lower()

    try:
        # Lightweight throttling to stay within Nominatim usage policy.
        time.sleep(0.1)
        prepared_request = requests.Request("GET", f"{NOMINATIM_BASE_URL}/search", params=params).prepare()
        logger.debug("Nominatim request URL: %s", prepared_request.url)
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params=params,
            timeout=10,
            headers={"User-Agent": "PropertyUnderwriter/1.0"},
        )
        response.raise_for_status()

        results = response.json()
        suggestions: List[Dict[str, str]] = []

        for result in results:
            address = result.get("address") or {}
            street = _extract_street_line(address)
            city = _extract_city(address)
            state = _normalize_state(address.get("state_code") or address.get("state"))
            postal_code = (address.get("postcode") or "").strip()

            description = _format_description(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                fallback=result.get("display_name", ""),
            )

            # Only return full addresses (street + city + state + ZIP)
            if not description or not _is_full_address(street, city, state, postal_code):
                logger.debug("Skipping Nominatim result without description: %s", result)
                continue

            suggestions.append(
                {
                    "description": description,
                    "place_id": str(result.get("place_id", "")),
                    "lat": result.get("lat", ""),
                    "lon": result.get("lon", ""),
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": postal_code,
                }
            )

        limited_suggestions = suggestions[: max(limit, 1)]
        logger.info(
            "Nominatim returned %d suggestions (requested %d) for query '%s'",
            len(limited_suggestions),
            limit,
            trimmed_query,
        )
        return limited_suggestions

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
        # Prefer the structured components if present.
        street = suggestion.get("street", "").strip()
        city = suggestion.get("city", "").strip()
        state = _normalize_state(suggestion.get("state"))
        postal_code = suggestion.get("zip", "").strip()

        if street and city and state:
            return Address(line1=street, city=city, state=state, zip=postal_code)

        description = suggestion.get("description", "")
        if not description:
            return None

        # Fallback to parsing the description when structured fields are missing.
        parts = [part.strip() for part in description.split(",")]
        if len(parts) < 3:
            return None

        import re

        line1 = parts[0].strip()

        city_candidate = ""
        state_candidate = ""
        zip_candidate = ""

        for part in parts:
            zip_match = re.search(r"\d{5}(-\d{4})?", part)
            if zip_match:
                zip_candidate = zip_match.group()
                break

        state_index = -1
        for idx, part in enumerate(parts):
            normalized_state = _normalize_state(part)
            if normalized_state:
                state_candidate = normalized_state
                state_index = idx
                break

        if state_candidate and state_index > 0:
            for i in range(state_index - 1, 0, -1):
                potential_city = parts[i].strip()
                if not any(word in potential_city.lower() for word in ["county", "parish", "borough", "township"]) and not _normalize_state(potential_city):
                    city_candidate = potential_city
                    break

        if not city_candidate and len(parts) >= 3:
            for i in range(1, min(4, len(parts))):
                potential_city = parts[i].strip()
                if not any(word in potential_city.lower() for word in ["county", "parish", "borough", "township", "state"]) and not _normalize_state(potential_city):
                    city_candidate = potential_city
                    break

        if line1 and city_candidate and state_candidate:
            return Address(line1=line1, city=city_candidate, state=state_candidate, zip=zip_candidate)

    except Exception as exc:
        logger.exception("Failed to parse Nominatim suggestion: %s", exc)

    return None
