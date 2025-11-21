"""RentCast client defaults and field mapping placeholders."""

BASE_URL: str = "https://api.rentcast.io/v1"
PROPERTY_ENDPOINT: str = "/properties"
VALUATION_ENDPOINT: str = "/avm/value"  # TODO: update if different

FIELD_MAPPINGS = {
    "beds": "bedrooms",
    "baths": "bathrooms",
    "sqft": "squareFootage",
    "lot_sqft": "lotSize",
    "year_built": "yearBuilt",
    "market_value_estimate": "value",  # when using valuation endpoint
    "rent_estimate": "rentEstimate",  # TODO: update if endpoint differs
    "annual_taxes": "propertyTaxes",  # nested, map in client
}

DEFAULT_TIMEOUT_SEC = 10
