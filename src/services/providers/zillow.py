from __future__ import annotations

from typing import Dict, Optional

import httpx

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class ZillowProvider(PropertyDataProvider):
    """Zillow property data provider - requires API key configuration."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int = 10,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or "https://api.bridgedataoutput.com/api/v2").rstrip("/")
        self.timeout = timeout

    def fetch(self, address: Address) -> Optional[PropertyData]:
        try:
            formatted_address = f"{address.line1}, {address.city}, {address.state} {address.zip}"

            property_data = self._search_property(formatted_address)
            if not property_data:
                logger.info("ZillowProvider: no property found for %s", formatted_address)
                return None

            zpid = property_data.get("zpid")
            if not zpid:
                logger.info("ZillowProvider: search result missing ZPID for %s", formatted_address)
                return None

            detailed_data = self._get_property_details(zpid)
            if not detailed_data:
                return None

            meta: Dict[str, str] = {}
            for key in ("zpid", "lastUpdated", "zestimateConfidence"):
                value = detailed_data.get(key)
                if value is not None:
                    meta[key] = str(value)

            return PropertyData(
                address=address,
                beds=detailed_data.get("bedrooms"),
                baths=detailed_data.get("bathrooms"),
                sqft=detailed_data.get("finishedSqFt"),
                lot_sqft=detailed_data.get("lotSizeSqFt"),
                year_built=detailed_data.get("yearBuilt"),
                market_value_estimate=detailed_data.get("zestimate"),
                rent_estimate=detailed_data.get("rentZestimate"),
                annual_taxes=detailed_data.get("taxAssessment"),
                closing_cost_estimate=None,
                meta=meta,
                sources=[ApiSource.ZILLOW],
            )

        except Exception as exc:  # pragma: no cover - defensive safety
            logger.exception("Error fetching Zillow data for %s: %s", address, exc)
            return None

    def _search_property(self, address: str) -> Optional[dict]:
        """Search for property by address to get ZPID."""
        headers = self._headers()
        params = {
            "access_token": self.api_key,
            "address": address,
        }

        response = self._get(f"{self.base_url}/properties", headers=headers, params=params)
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.error("ZillowProvider: failed to decode search response JSON")
            return None

        properties = payload.get("properties")
        if isinstance(properties, dict):
            properties = [properties]

        if not properties:
            bundle = payload.get("bundle") or {}
            if isinstance(bundle, dict):
                props = bundle.get("property")
                if isinstance(props, dict):
                    properties = [props]
                else:
                    properties = props

        if isinstance(properties, list) and properties:
            first = properties[0]
            if isinstance(first, dict):
                return first
            logger.error("ZillowProvider: unexpected property result type %s", type(first))
        elif properties:
            logger.error("ZillowProvider: unexpected properties payload type %s", type(properties))

        return None

    def _get_property_details(self, zpid: str) -> Optional[dict]:
        response = self._get(f"{self.base_url}/properties/{zpid}", headers=self._headers())
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.error("ZillowProvider: failed to decode detail response for %s", zpid)
            return None

        if isinstance(payload, dict):
            if "property" in payload and isinstance(payload["property"], dict):
                return payload["property"]
            return payload

        logger.error("ZillowProvider: unexpected detail payload type %s", type(payload))
        return None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[httpx.Response]:
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            logger.warning("ZillowProvider: HTTP error calling %s: %s", url, exc)
            return None

        if response.status_code == 429:
            logger.warning("ZillowProvider: rate limited when calling %s", url)
            return None

        if response.is_error:
            logger.error(
                "ZillowProvider: request to %s failed with status %s and body %s",
                url,
                response.status_code,
                response.text,
            )
            return None

        return response
