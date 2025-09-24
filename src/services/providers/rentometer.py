from __future__ import annotations
from typing import Dict, Optional

import requests

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class RentometerProvider(PropertyDataProvider):
    """Rentometer rental market data provider - requires API key configuration."""

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 10, default_bedrooms: int | None = None):
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

        try:
            response = requests.get(
                f"{self.base_url}/summary",
                params=params,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(
                    "RentometerProvider: request failed with status %s and body %s",
                    response.status_code,
                    response.text,
                )
                return None

            payload = response.json()
            data = payload.get("data") or {}
            rent_estimate = data.get("average") or data.get("median")
            if rent_estimate is None:
                return None

            meta: Dict[str, str] = {}
            for key in ("median", "percentile_25", "percentile_75", "sample_size"):
                if key in data and data[key] is not None:
                    meta[key] = str(data[key])

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

        except Exception as exc:
            logger.exception("RentometerProvider: error fetching data for %s: %s", formatted, exc)
            return None