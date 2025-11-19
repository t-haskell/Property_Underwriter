import json

import pytest

from src.core.models import Address, PropertyData
from src.utils.ai.mapper import (
    AddressPaths,
    AttributePath,
    PropertyDataMapper,
    PropertyDataMappingError,
    PropertyDataPaths,
)


class _DummyResponses:
    def __init__(self, return_value):
        self.return_value = return_value
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return self.return_value


class _DummyClient:
    def __init__(self, return_value):
        self.responses = _DummyResponses(return_value)


def _build_mapping():
    return PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["payload", "location", "line1"]),
            city=AttributePath(path=["payload", "location", "city"]),
            state=AttributePath(path=["payload", "location", "state"]),
            zip=AttributePath(path=["payload", "location", "postal"]),
        ),
        beds=AttributePath(path=["payload", "details", "summary", "beds"]),
        baths=AttributePath(path=["payload", "details", "summary", "baths"]),
        sqft=AttributePath(path=["payload", "details", "summary", "sq_ft"]),
        market_value_estimate=AttributePath(path=["payload", "valuation", "market"]),
    )


def test_mapper_builds_property_data_from_mapping():
    payload = {
        "payload": {
            "location": {"line1": "123 Main St", "city": "Austin", "state": "tx", "postal": "78701"},
            "details": {"summary": {"beds": 3, "baths": 2.5, "sq_ft": 1650}},
            "valuation": {"market": "415000"},
        }
    }
    mapping = _build_mapping()
    client = _DummyClient(mapping)
    mapper = PropertyDataMapper(client=client, model="test-model")

    result = mapper.map_property_data(payload, provider_name="rentcast")

    assert isinstance(result, PropertyData)
    assert result.address == Address(line1="123 Main St", city="Austin", state="TX", zip="78701")
    assert result.beds == 3
    assert result.baths == 2.5
    assert result.sqft == 1650
    assert result.market_value_estimate == 415000.0
    assert result.meta["address_line1_path"] == "payload.location.line1"
    assert result.meta["beds_path"] == "payload.details.summary.beds"

    [call] = client.responses.calls
    assert call["model"] == "test-model"
    assert "rentcast" in call["input"][1]["content"][0]["text"]
    assert json.dumps(payload, indent=2, sort_keys=True) in call["input"][1]["content"][0]["text"]


def test_mapper_supports_list_indexes_in_paths():
    payload = {
        "results": [
            {
                "location": {"line1": "400 Elm", "city": "Denver", "state": "CO", "postal": "80202"},
                "metrics": {"beds": 4, "baths": "3", "sq_ft": 2125},
            }
        ]
    }
    mapping = PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["results", "0", "location", "line1"]),
            city=AttributePath(path=["results", "0", "location", "city"]),
            state=AttributePath(path=["results", "0", "location", "state"]),
            zip=AttributePath(path=["results", "0", "location", "postal"]),
        ),
        beds=AttributePath(path=["results", "0", "metrics", "beds"]),
        baths=AttributePath(path=["results", "0", "metrics", "baths"]),
        sqft=AttributePath(path=["results", "0", "metrics", "sq_ft"]),
    )
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    result = mapper.map_property_data(payload)

    assert result.address.line1 == "400 Elm"
    assert result.beds == 4
    assert result.baths == 3.0
    assert result.sqft == 2125
    assert result.meta["address_line1_path"] == "results.0.location.line1"


def test_mapper_raises_when_address_incomplete():
    payload = {"data": {"value": 1}}
    mapping = PropertyDataPaths(address=AddressPaths(line1=None))
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    with pytest.raises(PropertyDataMappingError) as exc:
        mapper.map_property_data(payload)

    assert "Missing fields" in str(exc.value)


def test_mapper_can_return_mapping_with_property_data():
    payload = {"data": {"address": {"line1": "1", "city": "2", "state": "3", "zip": "4"}}}
    mapping = PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["data", "address", "line1"]),
            city=AttributePath(path=["data", "address", "city"]),
            state=AttributePath(path=["data", "address", "state"]),
            zip=AttributePath(path=["data", "address", "zip"]),
        )
    )
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    data, returned_mapping = mapper.map_property_data_with_paths(payload)

    assert isinstance(data, PropertyData)
    assert returned_mapping is mapping


def test_mapper_supports_list_payload_root():
    payload = [
        {
            "location": {"line1": "1 Ocean", "city": "Miami", "state": "FL", "postal": "33101"},
            "metrics": {"beds": 2, "baths": 2.0},
        }
    ]
    mapping = PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["0", "location", "line1"]),
            city=AttributePath(path=["0", "location", "city"]),
            state=AttributePath(path=["0", "location", "state"]),
            zip=AttributePath(path=["0", "location", "postal"]),
        ),
        beds=AttributePath(path=["0", "metrics", "beds"]),
    )
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    property_data = mapper.map_property_data(payload)

    assert property_data.address.line1 == "1 Ocean"
    assert property_data.meta["address_line1_path"] == "0.location.line1"


def test_mapper_allows_optional_fields_to_be_missing_when_paths_fail():
    payload = {"data": {"value": "not here"}}
    mapping = PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["data", "value"]),
            city=AttributePath(path=["data", "value", "city"]),
            state=AttributePath(path=["data", "value", "state"]),
            zip=AttributePath(path=["data", "value", "zip"]),
        ),
        beds=AttributePath(path=["data", "value", "beds"]),
    )
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    with pytest.raises(PropertyDataMappingError):
        mapper.map_property_data(payload)


def test_mapper_merely_skips_optional_fields_when_path_invalid():
    payload = {
        "payload": {
            "location": {"line1": "1", "city": "2", "state": "3", "postal": "4"},
            "details": {"summary": {"beds": 3}},
        }
    }
    mapping = PropertyDataPaths(
        address=AddressPaths(
            line1=AttributePath(path=["payload", "location", "line1"]),
            city=AttributePath(path=["payload", "location", "city"]),
            state=AttributePath(path=["payload", "location", "state"]),
            zip=AttributePath(path=["payload", "location", "postal"]),
        ),
        baths=AttributePath(path=["payload", "details", "summary", "baths"]),
    )
    mapper = PropertyDataMapper(client=_DummyClient(mapping))

    data = mapper.map_property_data(payload)

    assert data.baths is None
    assert "baths_path" not in data.meta


def test_mapper_appends_custom_instructions_to_prompt():
    mapping = _build_mapping()
    client = _DummyClient(mapping)
    mapper = PropertyDataMapper(client=client)

    mapper.map_property_data(
        {
            "payload": {
                "location": {"line1": "1", "city": "2", "state": "3", "postal": "4"},
                "details": {"summary": {"beds": 1, "baths": 1, "sq_ft": 500}},
                "valuation": {"market": 100},
            }
        },
        provider_name="provider-x",
        instructions="Only map data when it's verified",
    )

    [call] = client.responses.calls
    prompt = call["input"][0]["content"]
    assert isinstance(prompt, str)
    assert "Additional guidance" in prompt
    assert "Only map data when it's verified" in prompt
