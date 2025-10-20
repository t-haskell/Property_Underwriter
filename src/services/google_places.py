from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import requests

from ..core.models import Address
from ..utils.config import settings
from ..utils.logging import logger

AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class GooglePlacesError(RuntimeError):
    pass


def _is_enabled() -> bool:
    if not settings.GOOGLE_PLACES_API_KEY:
        logger.debug("Google Places API key not configured; autocomplete disabled.")
        return False
    return True


def get_place_suggestions(query: str, session_token: Optional[str] = None, country: Optional[str] = "us") -> List[Dict[str, str]]:
    if not _is_enabled():
        return []

    params: Dict[str, str] = {
        "input": query,
        "key": settings.GOOGLE_PLACES_API_KEY or "",
    }
    if session_token:
        params["sessiontoken"] = session_token
    if country:
        params["components"] = f"country:{country}"

    try:
        response = requests.get(AUTOCOMPLETE_URL, params=params, timeout=settings.PROVIDER_TIMEOUT_SEC)
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status")
        if status != "OK":
            logger.warning("Google Places autocomplete returned status %s", status)
            return []
        predictions = payload.get("predictions", [])
        return [
            {"description": p.get("description", ""), "place_id": p.get("place_id", "")}
            for p in predictions
            if p.get("place_id")
        ]
    except Exception as exc:
        logger.exception("Google Places autocomplete failed: %s", exc)
        return []


@lru_cache(maxsize=256)
def get_place_details(place_id: str, session_token: Optional[str] = None) -> Optional[Address]:
    if not _is_enabled():
        return None

    params: Dict[str, str] = {
        "place_id": place_id,
        "key": settings.GOOGLE_PLACES_API_KEY or "",
        "fields": "address_components",
    }
    if session_token:
        params["sessiontoken"] = session_token

    try:
        response = requests.get(DETAILS_URL, params=params, timeout=settings.PROVIDER_TIMEOUT_SEC)
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status")
        if status != "OK":
            logger.warning("Google Places details returned status %s", status)
            return None
        result = payload.get("result", {})
        components = result.get("address_components", [])
        return _parse_address_components(components)
    except Exception as exc:
        logger.exception("Google Places details lookup failed: %s", exc)
        return None


def _parse_address_components(components: List[Dict[str, object]]) -> Optional[Address]:
    mapping: Dict[str, str] = {}
    for component in components:
        long_name = component.get("long_name")
        short_name = component.get("short_name")
        types = component.get("types", [])
        if isinstance(types, list):
            for comp_type in types:
                mapping[str(comp_type)] = str(long_name or short_name or "")

    street_number = mapping.get("street_number", "").strip()
    route = mapping.get("route", "").strip()
    line1 = " ".join(part for part in [street_number, route] if part).strip()
    city = mapping.get("locality") or mapping.get("sublocality") or mapping.get("administrative_area_level_2") or ""
    state = mapping.get("administrative_area_level_1", "")
    postal_code = mapping.get("postal_code", "")

    if not (line1 and city and state and postal_code):
        logger.warning("Incomplete address components from Google Places: %s", mapping)
        return None

    return Address(line1=line1, city=city, state=state, zip=postal_code)
