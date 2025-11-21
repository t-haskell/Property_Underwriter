"""Configuration defaults for the Massachusetts MassGIS parcel layer.

Set ``BASE_URL`` and ``LAYER_ID`` to the statewide parcel feature service once
available. Land use code collections should be updated to match residential
and multi-family codes published by MassGIS.
"""

BASE_URL: str = ""  # TODO: fill with MassGIS ArcGIS base URL
LAYER_ID: str = ""  # TODO: fill with MassGIS parcel layer ID

FIELD_MAPPINGS = {
    "address": "SITE_ADDR",  # TODO: update with actual address field
    "city": "CITY_TOWN",  # TODO: update
    "state": "STATE",  # likely constant "MA"
    "zip": "ZIP",  # TODO: update
    "owner_name": "OWNER",  # TODO: update
    "assessed_land": "AV_LAND",  # TODO: update
    "assessed_building": "AV_BLDG",  # TODO: update
    "land_use_code": "LU",  # TODO: update
    "property_type": "USE_CODE_DESC",  # TODO: update
    "lot_sqft": "LOT_SIZE",  # TODO: update
    "year_built": "YEAR_BUILT",  # TODO: update
    "taxes": "TAXES",  # TODO: update
}

RESIDENTIAL_LAND_USE_CODES: set[str] = set()
MULTIFAMILY_LAND_USE_CODES: set[str] = set()

DEFAULT_TIMEOUT_SEC = 10
