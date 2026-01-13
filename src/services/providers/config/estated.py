"""Estated client defaults and field mapping placeholders."""

BASE_URL: str = "https://apis.estated.com/v4"
PROPERTY_ENDPOINT: str = "/property/"  # TODO: confirm final path

FIELD_MAPPINGS = {
    "beds": "bedrooms",
    "baths": "bathrooms",
    "sqft": "area.sqft",
    "lot_sqft": "area.lot",
    "year_built": "structure.year_built",
    "market_value_estimate": "valuation.value",
    "rent_estimate": "rent.estimate",  # TODO: update if available
    "annual_taxes": "taxes.annual",
    "owner_name": "owner.name",
    "property_type": "structure.type",
}

DEFAULT_TIMEOUT_SEC = 10
