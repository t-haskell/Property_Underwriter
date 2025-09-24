from __future__ import annotations

from typing import List, Optional

from src.core.models import Address, PropertyData
from src.utils.config import settings
from src.utils.logging import logger
from src.services.providers.attom import AttomProvider
from src.services.providers.base import PropertyDataProvider
from src.services.providers.closingcorp import ClosingcorpProvider
from src.services.providers.mock import MockProvider
from src.services.providers.rentometer import RentometerProvider
from src.services.providers.zillow import ZillowProvider


def merge(a: PropertyData, b: PropertyData) -> PropertyData:
    """Prefer non-null values from the newer record and combine metadata."""

    def prefer(new_value, existing_value):
        return new_value if new_value is not None else existing_value

    meta = {**a.meta, **b.meta}
    sources = list(dict.fromkeys([*a.sources, *b.sources]))

    if a.address != b.address:
        logger.warning("Merging property data with mismatched addresses: %s vs %s", a.address, b.address)

    return PropertyData(
        address=a.address or b.address,
        beds=prefer(b.beds, a.beds),
        baths=prefer(b.baths, a.baths),
        sqft=prefer(b.sqft, a.sqft),
        lot_sqft=prefer(b.lot_sqft, a.lot_sqft),
        year_built=prefer(b.year_built, a.year_built),
        market_value_estimate=prefer(b.market_value_estimate, a.market_value_estimate),
        rent_estimate=prefer(b.rent_estimate, a.rent_estimate),
        annual_taxes=prefer(b.annual_taxes, a.annual_taxes),
        closing_cost_estimate=prefer(b.closing_cost_estimate, a.closing_cost_estimate),
        meta=meta,
        sources=sources,
    )


def _configured_providers() -> List[PropertyDataProvider]:
    providers: List[PropertyDataProvider] = []

    if settings.ZILLOW_API_KEY:
        providers.append(
            ZillowProvider(
                api_key=settings.ZILLOW_API_KEY,
                base_url=settings.ZILLOW_BASE_URL,
                timeout=settings.PROVIDER_TIMEOUT_SEC,
            )
        )

    if settings.RENTOMETER_API_KEY:
        providers.append(
            RentometerProvider(
                api_key=settings.RENTOMETER_API_KEY,
                base_url=settings.RENTOMETER_BASE_URL,
                timeout=settings.PROVIDER_TIMEOUT_SEC,
                default_bedrooms=settings.RENTOMETER_DEFAULT_BEDROOMS,
            )
        )
    if settings.ATTOM_API_KEY:
        logger.info(f"Adding AttomProvider with API key: {settings.ATTOM_API_KEY}")
        providers.append(
            AttomProvider(
                api_key=settings.ATTOM_API_KEY,
                base_url=settings.ATTOM_BASE_URL,
                timeout=settings.PROVIDER_TIMEOUT_SEC,
            )
        )
    if settings.CLOSINGCORP_API_KEY:
        providers.append(
            ClosingcorpProvider(
                api_key=settings.CLOSINGCORP_API_KEY,
                base_url=settings.CLOSINGCORP_BASE_URL,
                timeout=settings.PROVIDER_TIMEOUT_SEC,
            )
        )

    if not providers and settings.USE_MOCK_PROVIDER_IF_NO_KEYS:
        providers.append(MockProvider())

    return providers

def normalize_address(address: Address) -> Address:
    return Address(
        line1=address.line1.strip().upper() ,
        city=address.city.strip().upper(),
        state=address.state.strip().upper(),
        zip=address.zip.strip(),
    )


def fetch_property(address: Address, use_mock_if_empty: bool = True) -> Optional[PropertyData]:
    providers = _configured_providers()
    logger.info(f"Configured providers: {providers}")

    # NORMALIZING THE ADDRESS
    address = normalize_address(address)

    if not providers and use_mock_if_empty:
        providers = [MockProvider()]

    if not providers:
        logger.warning("No property data providers configured; returning None.")
        return None

    merged: Optional[PropertyData] = None
    for provider in providers:
        try:
            data = provider.fetch(address)
            logger.info(f"Data fetched with {provider}: {data}")
        except Exception as exc:
            logger.exception("Provider %s failed: %s", provider.__class__.__name__, exc)
            continue

        if not data:
            logger.info("Provider %s returned no data for %s", provider.__class__.__name__, address)
            continue

        merged = data if merged is None else merge(merged, data)

    return merged