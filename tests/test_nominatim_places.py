"""Tests for Nominatim suggestion utilities."""

from src.core.models import Address
from src.services.nominatim_places import get_address_from_suggestion


def test_get_address_from_structured_suggestion() -> None:
    suggestion = {
        "street": "123 Main St",
        "city": "Boston",
        "state": "ma",
        "zip": "02108",
        "description": "123 Main St, Boston, MA 02108",
    }

    address = get_address_from_suggestion(suggestion)

    assert address == Address(line1="123 Main St", city="Boston", state="MA", zip="02108")


def test_get_address_from_description_fallback() -> None:
    suggestion = {
        "description": "123 Main Street, Boston, Suffolk County, Massachusetts, 02108, United States",
    }

    address = get_address_from_suggestion(suggestion)

    assert address == Address(line1="123 Main Street", city="Boston", state="MA", zip="02108")
