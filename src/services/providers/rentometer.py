from __future__ import annotations

from typing import Dict, Optional

import httpx

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class RentometerProvider(PropertyDataProvider):
    """Rentometer rental market data provider - requires API key configuration."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int = 10,
        default_bedrooms: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or "https://www.rentometer.com/api/v1").rstrip("/")
        self.timeout = timeout
        self.default_bedrooms = default_bedrooms

    def fetch(self, address: Address) -> Optional[PropertyData]:
        formatted = f"{address.line1}, {address.city}, {address.state} {address.zip}"
        params: Dict[str, str] = {
            "api_key": self.api_key,
            "address": formatted,
        }

        if self.default_bedrooms is not None:
            params["bedrooms"] = str(self.default_bedrooms)

        response = self._get(f"{self.base_url}/summary", params=params)
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.error("RentometerProvider: failed to decode response JSON for %s", formatted)
            return None

        data = payload.get("data") or {}
        if not isinstance(data, dict):
            logger.error("RentometerProvider: unexpected payload shape: %s", payload)
            return None

        rent_estimate = data.get("average") or data.get("median")
        if rent_estimate is None:
            logger.info("RentometerProvider: no rent estimate available for %s", formatted)
            return None

        meta: Dict[str, str] = {}
        for key in ("median", "percentile_25", "percentile_75", "sample_size"):
            value = data.get(key)
            if value is not None:
                meta[key] = str(value)

        return PropertyData(
            address=address,
            beds=None,
            baths=None,
            sqft=None,
            lot_sqft=None,
            year_built=None,
            market_value_estimate=None,
            rent_estimate=rent_estimate,
            annual_taxes=None,
            closing_cost_estimate=None,
            meta=meta,
            sources=[ApiSource.RENTOMETER],
        )

    def _get(self, url: str, params: Dict[str, str]) -> Optional[httpx.Response]:
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            logger.warning("RentometerProvider: HTTP error calling %s: %s", url, exc)
            return None

        if response.status_code == 429:
            logger.warning("RentometerProvider: rate limited when calling %s", url)
            return None

        if response.is_error:
            logger.error(
                "RentometerProvider: request failed with status %s and body %s",
                response.status_code,
                response.text,
            )
            return None

        return response
