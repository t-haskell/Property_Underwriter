"""Configuration defaults for the Maryland MD iMAP parcel feature service.

Populate the ``BASE_URL`` and ``LAYER_ID`` constants with the authoritative
ArcGIS REST endpoint for the MD iMAP Parcel Points layer. Field mappings are
kept explicit so they can be tuned without code changes once the schema is
finalised.
"""

BASE_URL: str = ""  # TODO: fill with MD iMAP ArcGIS base URL
LAYER_ID: str = ""  # TODO: fill with MD iMAP parcel layer ID

FIELD_MAPPINGS = {
    "address": "SITUSADDR",  # TODO: update with actual address field
    "city": "SITE_CITY",  # TODO: update
    "state": "STATE",  # likely constant "MD"
    "zip": "ZIPCODE",  # TODO: update
    "owner_name": "OWNNAM1",  # TODO: update
    "assessed_land": "LANDAREA",  # TODO: update
    "assessed_building": "BLDGAREA",  # TODO: update
    "land_use_code": "LANDUSE",  # TODO: update
    "property_type": "STRUCTURETYPE",  # TODO: update
    "lot_sqft": "LOTSQFT",  # TODO: update
    "year_built": "YEARBUILT",  # TODO: update
    "taxes": "ANNLTAXES",  # TODO: update
}

RESIDENTIAL_LAND_USE_CODES: set[str] = set()
MULTIFAMILY_LAND_USE_CODES: set[str] = set()


DEFAULT_TIMEOUT_SEC = 10
