from __future__ import annotations

from typing import List, Optional

from ..core.models import Address, PropertyData
from ..utils.config import settings
from ..utils.logging import logger
from .providers.attom import AttomProvider
from .providers.base import PropertyDataProvider
from .providers.closingcorp import ClosingcorpProvider
from .providers.mock import MockProvider
from .providers.rentometer import RentometerProvider
from .providers.zillow import ZillowProvider


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

    zillow_config = settings.zillow
    if zillow_config.api_key:
        providers.append(
            ZillowProvider(
                api_key=zillow_config.api_key,
                base_url=zillow_config.base_url,
                timeout=zillow_config.timeout,
            )
        )

    rentometer_config = settings.rentometer
    if rentometer_config.api_key:
        providers.append(
            RentometerProvider(
                api_key=rentometer_config.api_key,
                base_url=rentometer_config.base_url,
                timeout=rentometer_config.timeout,
                default_bedrooms=rentometer_config.default_bedrooms,
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

    return providers

def normalize_address(address: Address) -> Address:
    return Address(
        line1=address.line1.strip().upper() ,
        city=address.city.strip().upper(),
        state=address.state.strip().upper(),
        zip=address.zip.strip(),
    )


def fetch_property(
    address: Address, use_mock_if_empty: Optional[bool] = None
) -> Optional[PropertyData]:
    if use_mock_if_empty is None:
        use_mock_if_empty = settings.USE_MOCK_PROVIDER_IF_NO_KEYS

    providers = _configured_providers()
    logger.info(f"Configured providers: {providers}")

    # NORMALIZING THE ADDRESS
    address = normalize_address(address)

    if not providers:
        if use_mock_if_empty:
            logger.info("No providers configured; using mock fallback.")
            return MockProvider().fetch(address)
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

    if merged:
        return merged

    if use_mock_if_empty:
        logger.info("No provider returned data; using mock fallback for %s", address)
        try:
            return MockProvider().fetch(address)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("MockProvider failed to generate fallback data: %s", exc)
            return None

    return None
