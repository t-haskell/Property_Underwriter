from __future__ import annotations

from typing import List, Optional

from ..core.models import Address, PropertyData
from ..utils.config import settings
from ..utils.logging import logger
from .data_providers import (
    DataAggregationService,
    HudFmrProvider,
    MarketplaceCompsProvider,
)
from .property_merging import (
    ProviderCache,
    ProviderName,
    NormalizedPropertyRecord,
    cached_record_key,
    merge_property_records,
    normalize_property_data,
)
from .providers.config import mass_gis, md_imap
from .providers.estated_client import EstatedClient, normalize_estated
from .providers.attom import AttomProvider
from .providers.base import PropertyDataProvider
from .providers.closingcorp import ClosingcorpProvider
from .providers.estated import EstatedProvider
from .providers.mass_gis_client import MassGisClient, normalize_mass_gis
from .providers.mock import MockProvider
from .providers.md_imap_client import MdImapClient, normalize_md_imap
from .providers.rentometer import RentometerProvider
from .providers.rentcast import RentcastProvider
from .providers.rentcast_client import RentcastClient, normalize_rentcast
from .providers.redfin import RedfinProvider
from .providers.zillow import ZillowProvider
from .persistence import get_repository


_provider_cache = ProviderCache(settings.CACHE_TTL_MIN)


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
            )
        )

    estated_config = settings.estated
    if estated_config.api_key:
        providers.append(
            EstatedProvider(
                api_key=estated_config.api_key,
                base_url=estated_config.base_url,
                timeout=estated_config.timeout,
            )
        )

    rentcast_config = settings.rentcast
    if rentcast_config.api_key:
        providers.append(
            RentcastProvider(
                api_key=rentcast_config.api_key,
                base_url=rentcast_config.base_url,
                timeout=rentcast_config.timeout,
            )
        )

    redfin_config = settings.redfin
    if redfin_config.api_key:
        providers.append(
            RedfinProvider(
                api_key=redfin_config.api_key,
                base_url=redfin_config.base_url,
                timeout=redfin_config.timeout,
                host=redfin_config.host,
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


def _build_aggregation_service(
    providers: List[PropertyDataProvider],
) -> DataAggregationService:
    hud_config = settings.hud
    open_data_providers = []
    if hud_config.base_url:
        open_data_providers.append(
            HudFmrProvider(
                base_url=hud_config.base_url,
                api_key=hud_config.api_key,
                timeout=hud_config.timeout,
                cache_ttl_min=hud_config.cache_ttl_min,
            )
        )

    marketplace_config = settings.marketplace
    marketplace_provider = None
    if marketplace_config.enabled:
        marketplace_provider = MarketplaceCompsProvider(
            base_url=marketplace_config.base_url,
            api_key=marketplace_config.api_key,
            enabled=marketplace_config.enabled,
            timeout=marketplace_config.timeout,
            max_results=marketplace_config.max_results,
            max_retries=marketplace_config.max_retries,
            backoff_seconds=marketplace_config.backoff_seconds,
        )

    return DataAggregationService(
        primary_providers=providers,
        open_data_providers=open_data_providers,
        marketplace_provider=marketplace_provider,
    )


def _fetch_with_cache(
    provider_name: str,
    address: Address,
    fetch_fn,
    normalize_fn,
):  # noqa: ANN001
    cache_key = cached_record_key(provider_name, address)
    cached_record = _provider_cache.get(cache_key)
    if cached_record:
        return cached_record

    result = fetch_fn(address)
    if result is None:
        return None

    normalized = normalize_fn(result)
    _provider_cache.set(cache_key, normalized)
    return normalized


def _collect_normalized_records(
    address: Address, cached: PropertyData | None
) -> List[NormalizedPropertyRecord]:
    records: List[NormalizedPropertyRecord] = []

    if cached:
        records.append(normalize_property_data(ProviderName.CACHED, cached, raw=cached.meta))

    if address.state == "MD":
        md_config = settings.md_imap
        if md_config.base_url and md_config.layer_id:
            md_client = MdImapClient(md_config.base_url, md_config.layer_id, timeout=md_config.timeout)
            record = _fetch_with_cache(ProviderName.MD_IMAP, address, md_client.get_by_address, normalize_md_imap)
            if record and _is_residential(record):
                records.append(record)

    if address.state == "MA":
        ma_config = settings.mass_gis
        if ma_config.base_url and ma_config.layer_id:
            ma_client = MassGisClient(ma_config.base_url, ma_config.layer_id, timeout=ma_config.timeout)
            record = _fetch_with_cache(ProviderName.MASS_GIS, address, ma_client.get_by_address, normalize_mass_gis)
            if record and _is_residential(record):
                records.append(record)

    if settings.rentcast.api_key:
        rentcast_client = RentcastClient(
            api_key=settings.rentcast.api_key,
            base_url=settings.rentcast.base_url,
            timeout=settings.rentcast.timeout,
        )
        record = _fetch_with_cache(ProviderName.RENTCAST, address, rentcast_client.get_by_address, normalize_rentcast)
        if record:
            records.append(record)

    if settings.estated.api_key:
        estated_client = EstatedClient(
            api_key=settings.estated.api_key,
            base_url=settings.estated.base_url,
            timeout=settings.estated.timeout,
        )
        record = _fetch_with_cache(ProviderName.ESTATED, address, estated_client.get_by_address, normalize_estated)
        if record:
            records.append(record)

    return records


def _is_residential(record: NormalizedPropertyRecord) -> bool:
    if record.provider == ProviderName.MD_IMAP:
        if md_imap.RESIDENTIAL_LAND_USE_CODES:
            return record.land_use_code in md_imap.RESIDENTIAL_LAND_USE_CODES
        return True
    if record.provider == ProviderName.MASS_GIS:
        if mass_gis.RESIDENTIAL_LAND_USE_CODES:
            return record.land_use_code in mass_gis.RESIDENTIAL_LAND_USE_CODES
        return True
    return True

def normalize_address(address: Address) -> Address:
    return Address(
        line1=address.line1.strip().upper(),
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

    repository = get_repository()
    normalized_address = normalize_address(address)

    cached = repository.get_property(normalized_address)
    if cached:
        has_raw_payload = any(
            key.lower().endswith("_raw") for key in (cached.meta or {}).keys()
        )
        if has_raw_payload:
            logger.info(
                "Returning cached property data for %s from persistence store (with raw)",
                normalized_address,
            )
            return cached
        logger.info(
            "Cached property found for %s but missing provider raw payload; attempting refresh",
            normalized_address,
        )

    normalized_records = _collect_normalized_records(normalized_address, cached)
    has_live_records = any(record.provider != ProviderName.CACHED for record in normalized_records)

    if has_live_records:
        try:
            merged = merge_property_records(normalized_records)
        except ValueError:
            merged = None
        if merged:
            repository.upsert_property(merged.property)
            return merged.property

    address = normalized_address
    aggregation_service = _build_aggregation_service(providers)
    if not providers and not aggregation_service.open_data_providers and not aggregation_service.marketplace_provider:
        if cached:
            logger.info(
                "No providers configured; returning cached property data for %s",
                normalized_address,
            )
            return cached
        if use_mock_if_empty:
            logger.info("No providers configured; using mock fallback.")
            result = MockProvider().fetch(address)
            if result:
                repository.upsert_property(result)
            return result
        logger.warning("No property data providers configured; returning None.")
        return None

    aggregated = aggregation_service.aggregate(address, existing=cached)

    has_payload = any(
        getattr(aggregated, field) is not None
        for field in (
            "beds",
            "baths",
            "sqft",
            "lot_sqft",
            "year_built",
            "market_value_estimate",
            "rent_estimate",
            "annual_taxes",
            "closing_cost_estimate",
        )
    ) or bool(aggregated.meta)

    if aggregated and has_payload:
        repository.upsert_property(aggregated)
        return aggregated

    if cached:
        logger.info(
            "Providers returned no new data for %s; falling back to cached property snapshot",
            address,
        )
        return cached

    if use_mock_if_empty:
        logger.info("No provider returned data; using mock fallback for %s", address)
        try:
            result = MockProvider().fetch(address)
            if result:
                repository.upsert_property(result)
            return result
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("MockProvider failed to generate fallback data: %s", exc)
            return None

    return None
