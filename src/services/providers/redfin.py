from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse

import httpx

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class RedfinProvider(PropertyDataProvider):
    """Redfin property data provider using the RapidAPI gateway."""

    DETAILS_ENDPOINT = "/detailsByAddress"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        *,
        timeout: int = 10,
        host: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("RedfinProvider requires a non-empty API key")

        self.api_key = api_key
        self.base_url = (base_url or "https://redfin-working-api1.p.rapidapi.com").rstrip("/")
        parsed_host = host or urlparse(self.base_url).netloc
        self.host = parsed_host or "redfin-working-api1.p.rapidapi.com"
        self.timeout = timeout

    def fetch(self, address: Address) -> Optional[PropertyData]:
        formatted = f"{address.line1}, {address.city}, {address.state} {address.zip}"
        payload = self._details_by_address(formatted)
        if payload is None:
            return None

        meta: Dict[str, str] = {"redfin_raw": json.dumps(payload)}

        primary = self._extract_primary_section(payload)
        beds = self._find_first(primary, {"beds", "bedrooms", "bedRooms"})
        baths = self._find_first(
            primary,
            {"baths", "bathrooms", "bathRooms", "bathsDecimal", "bathRoomsTotal"},
        )
        sqft = self._find_first(primary, {"sqft", "squareFeet", "livingArea", "finishedSqft"})
        lot_sqft = self._find_first(
            primary,
            {"lotSqFt", "lotSizeSqFt", "lotSquareFeet", "lotSize"},
        )
        year_built = self._find_first(primary, {"yearBuilt", "builtYear"})
        market_value = self._find_first(
            primary,
            {
                "redfinEstimate",
                "estimate",
                "marketValue",
                "homeEstimate",
                "propertyValue",
            },
        )
        rent_estimate = self._find_first(primary, {"rentEstimate", "rentValue"})
        annual_taxes = self._find_first(primary, {"annualTax", "propertyTax", "taxAnnual"})

        property_id = self._find_first(primary, {"propertyId", "listingId", "mlsId", "property_id"})
        if property_id is not None:
            meta["redfin_property_id"] = str(property_id)

        detail_url = self._find_first(primary, {"url", "detailUrl", "homeUrl"})
        if detail_url is not None:
            meta["redfin_url"] = str(detail_url)

        return PropertyData(
            address=address,
            beds=beds,
            baths=baths,
            sqft=sqft,
            lot_sqft=lot_sqft,
            year_built=year_built,
            market_value_estimate=market_value,
            rent_estimate=rent_estimate,
            annual_taxes=annual_taxes,
            closing_cost_estimate=None,
            meta=meta,
            sources=[ApiSource.REDFIN],
        )

    def _details_by_address(self, address: str) -> Optional[dict]:
        response = self._get(
            f"{self.base_url}{self.DETAILS_ENDPOINT}",
            params={"address": address},
        )
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.error("RedfinProvider: failed to decode JSON for %s", address)
            return None

        status = str(payload.get("status", "")).lower() if isinstance(payload, dict) else ""
        if status and status not in {"ok", "success"}:
            logger.info("RedfinProvider: API returned status '%s' for %s", status, address)

        return payload

    def _get(self, url: str, params: Dict[str, str]) -> Optional[httpx.Response]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host,
            "Accept": "application/json",
        }
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            logger.warning("RedfinProvider: HTTP error calling %s: %s", url, exc)
            return None

        if response.status_code == 429:
            logger.warning("RedfinProvider: rate limited when calling %s", url)
            return None

        if response.is_error:
            logger.error(
                "RedfinProvider: request to %s failed with status %s and body %s",
                url,
                response.status_code,
                response.text,
            )
            return None

        return response

    @staticmethod
    def _extract_primary_section(payload: dict) -> Any:
        if isinstance(payload, dict):
            for key in ("result", "data", "payload", "propertyDetail", "property"):
                value = payload.get(key)
                if isinstance(value, (dict, list)):
                    return value
        return payload

    @staticmethod
    def _find_first(payload: Any, keys: Iterable[str]) -> Optional[Any]:
        if payload is None:
            return None

        queue: list[Any] = [payload]
        sought = set(keys)
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                for key, value in current.items():
                    if key in sought and value not in (None, ""):
                        return value
                    if isinstance(value, (dict, list)):
                        queue.append(value)
            elif isinstance(current, list):
                queue.extend(current)

        return None
