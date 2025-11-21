from datetime import UTC, datetime

from src.core.models import Address
from src.services.property_merging import (
    FieldSourceInfo,
    ProviderName,
    NormalizedPropertyRecord,
    merge_property_records,
)
from src.services.providers.md_imap_client import MdImapProperty, normalize_md_imap
from src.services.providers.mass_gis_client import MassGisProperty, normalize_mass_gis


def _base_address() -> Address:
    return Address(line1="123 MAIN ST", city="ANYTOWN", state="MD", zip="12345")


def test_normalize_md_imap_includes_land_use_meta():
    address = _base_address()
    md_property = MdImapProperty(
        address=address,
        lot_sqft=5000,
        year_built=1985,
        annual_taxes=2100.0,
        land_use_code="R1",
        property_type="Single Family",
    )

    normalized = normalize_md_imap(md_property)

    assert normalized.provider == ProviderName.MD_IMAP
    assert normalized.lot_sqft == 5000
    assert normalized.meta["landUseCode"] == "R1"
    assert normalized.meta["propertyType"] == "Single Family"


def test_normalize_mass_gis_flags_owner():
    address = Address(line1="45 Park Ave", city="Boston", state="MA", zip="02115")
    record = MassGisProperty(
        address=address,
        owner_name="Example Owner",
        land_use_code="112",
        property_type="Apartment",
    )

    normalized = normalize_mass_gis(record)

    assert normalized.provider == ProviderName.MASS_GIS
    assert normalized.owner_name == "Example Owner"
    assert normalized.meta["ownerName"] == "Example Owner"


def test_merge_prioritises_assessor_for_static_fields():
    address = _base_address()
    md_record = NormalizedPropertyRecord(
        provider=ProviderName.MD_IMAP,
        fetched_at=datetime.now(UTC),
        address=address,
        lot_sqft=4000,
        year_built=1975,
        annual_taxes=1900.0,
        land_use_code="R2",
        property_type="Single Family",
        raw={},
    )
    estated_record = NormalizedPropertyRecord(
        provider=ProviderName.ESTATED,
        fetched_at=datetime.now(UTC),
        address=address,
        lot_sqft=3500,
        year_built=1980,
        annual_taxes=2100.0,
        market_value_estimate=325000.0,
        raw={},
    )
    rentcast_record = NormalizedPropertyRecord(
        provider=ProviderName.RENTCAST,
        fetched_at=datetime.now(UTC),
        address=address,
        market_value_estimate=350000.0,
        rent_estimate=2500.0,
        raw={},
    )

    merged = merge_property_records([estated_record, rentcast_record, md_record])

    property_data = merged.property
    assert property_data.lot_sqft == 4000
    assert property_data.year_built == 1975
    assert property_data.annual_taxes == 1900.0
    assert property_data.market_value_estimate == 350000.0
    assert property_data.rent_estimate == 2500.0

    assert property_data.meta["lot_sqft.source"] == ProviderName.MD_IMAP
    assert property_data.meta["market_value_estimate.source"] == ProviderName.RENTCAST

    providers = {entry.provider for entry in merged.field_sources if isinstance(entry, FieldSourceInfo)}
    assert ProviderName.MD_IMAP in providers
    assert ProviderName.RENTCAST in providers
