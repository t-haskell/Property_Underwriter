"""LLM powered helpers for extracting :class:`~src.core.models.PropertyData` from JSON payloads.

The module provides a small facade over OpenAI's structured output API that asks the
model to describe where relevant bits of property information live inside an
arbitrary JSON response.  The discovered paths are then followed deterministically
within Python which keeps the LLM out of the critical conversion loop while still
benefiting from its reasoning capabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union

try:  # pragma: no cover - exercised when dependency is available
    from openai import OpenAI
except ImportError:  # pragma: no cover - allows tests without installing openai
    OpenAI = None  # type: ignore[assignment]
from pydantic import BaseModel, ConfigDict, Field

from src.core.models import Address, PropertyData
from src.utils.config import settings
from src.utils.logging import logger


DEFAULT_MODEL_NAME = settings.OPENAI_MODEL or "gpt-4o-mini"

# JSON payloads we receive from providers are typically either an object (mapping)
# or a list.  Defining an alias makes intent clearer for type-checkers and readers.
JSONDocument = Union[Mapping[str, Any], Sequence[Any]]


class PropertyDataMappingError(RuntimeError):
    """Raised when the LLM mapping cannot be converted into :class:`PropertyData`."""


class AttributePath(BaseModel):
    """Represents a model-discovered attribute path within a JSON document.

    Each ``path`` entry corresponds to either a mapping key or a list index.  The
    mapper converts list indexes to integers during traversal but stores the
    traversed segments as strings in the resulting metadata for readability.
    """

    path: Optional[List[str]] = Field(
        default=None,
        description="Sequence of keys (or list indexes) that lead to the value.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Optional free-form note on why the attribute was selected.",
    )

    model_config = ConfigDict(extra="ignore")


class AddressPaths(BaseModel):
    line1: Optional[AttributePath] = None
    city: Optional[AttributePath] = None
    state: Optional[AttributePath] = None
    zip: Optional[AttributePath] = Field(
        default=None,
        description="Zip or postal code path.",
    )

    model_config = ConfigDict(extra="ignore")


class PropertyDataPaths(BaseModel):
    """Structured output returned by the LLM for property level fields."""

    address: AddressPaths = Field(default_factory=AddressPaths)
    beds: Optional[AttributePath] = None
    baths: Optional[AttributePath] = None
    sqft: Optional[AttributePath] = None
    lot_sqft: Optional[AttributePath] = None
    year_built: Optional[AttributePath] = None
    market_value_estimate: Optional[AttributePath] = None
    rent_estimate: Optional[AttributePath] = None
    annual_taxes: Optional[AttributePath] = None
    closing_cost_estimate: Optional[AttributePath] = None

    model_config = ConfigDict(extra="ignore")


@dataclass(slots=True)
class _ValueResolution:
    """Holds the resolved value and the path used to compute it."""

    value: Any
    path: Sequence[str]


def _follow_path(payload: JSONDocument, path: Sequence[str]) -> Optional[_ValueResolution]:
    """Traverse ``payload`` following ``path`` returning the resolved value.

    The traversal is intentionally strict.  Missing keys, invalid list indexes or
    attempts to index non-traversable values immediately abort the resolution and
    return ``None``.  This ensures we never fabricate values when the upstream LLM
    guessed incorrectly.
    """
    current = payload
    traversed: list[str] = []

    for segment in path:
        traversed.append(segment)
        if isinstance(current, Mapping):
            if segment not in current:
                logger.debug("Path segment missing in mapping", extra={"segment": segment, "path": path})
                return None
            current = current[segment]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                index = int(segment)
            except ValueError:
                logger.debug(
                    "Non-numeric segment provided for list traversal",
                    extra={"segment": segment, "path": path},
                )
                return None
            if index < 0 or index >= len(current):
                logger.debug(
                    "List index out of range during traversal",
                    extra={"index": index, "path": path},
                )
                return None
            current = current[index]
        else:
            logger.debug(
                "Encountered non-traversable object while following path",
                extra={"segment": segment, "path": path},
            )
            return None
    return _ValueResolution(current, traversed)


class PropertyDataMapper:
    """Use an OpenAI Responses model to discover property data values in arbitrary JSON payloads."""

    def __init__(self, *, client: Optional[Any] = None, model: str = DEFAULT_MODEL_NAME) -> None:
        if client is None:
            if OpenAI is None:
                raise RuntimeError(
                    "openai package is required when no client is provided. Install the 'openai' dependency."
                )
            if not settings.OPENAI_API_KEY:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured. Provide a client explicitly or set the environment variable."
                )
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._client = client
        self._model = model

    def map_property_data(
        self,
        payload: JSONDocument,
        *,
        provider_name: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> PropertyData:
        """Extract a :class:`PropertyData` instance from an API payload.

        Parameters
        ----------
        payload:
            The JSON response to analyse.  It can be a mapping/dictionary or a
            list (for payloads that wrap the interesting object in the first
            element).
        provider_name:
            Optional name of the upstream provider.  When supplied the value is
            baked into the LLM prompt which helps it reason about field
            conventions.
        instructions:
            Additional instructions appended verbatim to the system prompt.  Use
            this to steer the model towards provider specific quirks.

        Returns
        -------
        PropertyData
            A domain model with any resolvable attributes populated.

        Raises
        ------
        PropertyDataMappingError
            Raised when the model provided paths for the address but we were not
            able to resolve all mandatory address fields.
        RuntimeError
            Propagated from the constructor if the OpenAI client cannot be
            initialised.
        """

        data, _ = self.map_property_data_with_paths(
            payload,
            provider_name=provider_name,
            instructions=instructions,
        )
        return data

    def map_property_data_with_paths(
        self,
        payload: JSONDocument,
        *,
        provider_name: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> Tuple[PropertyData, PropertyDataPaths]:
        """Return both the mapped :class:`PropertyData` and the structured attribute paths.

        The structured paths can be persisted alongside the property data to aid
        future troubleshooting or to prime the mapper for similar payloads.
        """

        logger.debug(
            "Requesting property data mapping",
            extra={"provider": provider_name, "model": self._model},
        )
        mapping = self._request_mapping(
            payload, provider_name=provider_name, instructions=instructions
        )
        property_data = self._build_property_data(payload, mapping)
        return property_data, mapping

    def _request_mapping(
        self,
        payload: JSONDocument,
        *,
        provider_name: Optional[str],
        instructions: Optional[str],
    ) -> PropertyDataPaths:
        """Ask the LLM for the attribute paths that map payload values.

        Wrapping the call makes it easy to stub in tests and to add consistent
        logging and error handling when the API is unavailable.
        """
        base_instructions = (
            "You are a meticulous analyst helping map property related fields in JSON responses. "
            "Return the paths that lead to address, bed/bath counts, square footage, valuation metrics, "
            "and other financial fields when available. Each path must be an ordered list of keys that "
            "navigates the JSON without guessing missing steps. If you cannot find a value, leave the path null."
        )
        if instructions:
            base_instructions = f"{base_instructions}\nAdditional guidance: {instructions.strip()}"

        request_json = json.dumps(payload, indent=2, sort_keys=True)
        provider_info = provider_name or "unknown provider"
        logger.debug(
            "Submitting structured output request to OpenAI",
            extra={"provider": provider_info, "model": self._model},
        )
        try:
            response = self._client.responses.parse(
                model=self._model,
                input=[
                    {
                        "role": "system",
                        "content": base_instructions,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyse the following JSON payload from {provider} and identify the paths to property "
                                "attributes required for the PropertyData model.\n\nJSON:\n{json_payload}".format(
                                    provider=provider_info, json_payload=request_json
                                ),
                            }
                        ],
                    },
                ],
                response_format=PropertyDataPaths,
            )
        except Exception as exc:  # pragma: no cover - network/runtime failures are rare and hard to simulate
            raise RuntimeError("Failed to fetch property data mapping from OpenAI") from exc

        if not isinstance(response, PropertyDataPaths):
            raise TypeError(
                "Unexpected response type from OpenAI structured output parser; "
                "expected PropertyDataPaths but received "
                f"{type(response)!r}"
            )

        return response

    def _build_property_data(self, payload: JSONDocument, mapping: PropertyDataPaths) -> PropertyData:
        meta: dict[str, str] = {}

        address_kwargs = self._collect_address(payload, mapping.address, meta)
        if set(address_kwargs) != {"line1", "city", "state", "zip"}:
            missing = {"line1", "city", "state", "zip"} - set(address_kwargs)
            raise PropertyDataMappingError(
                f"Unable to construct address from mapping. Missing fields: {', '.join(sorted(missing))}"
            )

        property_kwargs: dict[str, Any] = {
            "address": Address(**address_kwargs),
            "meta": meta,
        }
        for field_name in (
            "beds",
            "baths",
            "sqft",
            "lot_sqft",
            "year_built",
            "market_value_estimate",
            "rent_estimate",
            "annual_taxes",
            "closing_cost_estimate",
        ):
            attribute = getattr(mapping, field_name)
            resolved = self._resolve_attribute(payload, attribute)
            if resolved is not None:
                property_kwargs[field_name] = resolved.value
                meta[field_name + "_path"] = _format_path(resolved.path)

        return PropertyData(**property_kwargs)

    def _collect_address(
        self,
        payload: JSONDocument,
        address_paths: AddressPaths,
        meta: dict[str, str],
    ) -> dict[str, Any]:
        address_values: dict[str, Any] = {}
        for field_name in ("line1", "city", "state", "zip"):
            attribute = getattr(address_paths, field_name)
            resolved = self._resolve_attribute(payload, attribute)
            if resolved is not None:
                address_values[field_name] = resolved.value
                meta[f"address_{field_name}_path"] = _format_path(resolved.path)
        return address_values

    def _resolve_attribute(
        self,
        payload: JSONDocument,
        attribute: Optional[AttributePath],
    ) -> Optional[_ValueResolution]:
        if attribute is None or attribute.path is None:
            return None
        resolution = _follow_path(payload, attribute.path)
        if resolution is None:
            return None
        logger.debug(
            "Resolved attribute via path",
            extra={"path": resolution.path, "value_preview": str(resolution.value)[:80]},
        )
        return resolution


def _format_path(path: Sequence[str]) -> str:
    return ".".join(str(segment) for segment in path)


__all__ = [
    "PropertyDataMapper",
    "PropertyDataMappingError",
    "AttributePath",
    "PropertyDataPaths",
]
