from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional

import httpx

from ...core.models import Address, ApiSource
from ...utils.logging import logger
from .base import BaseDataProvider
from .models import ProviderMetadata, ProviderResult, PropertyDataPatch


class MarketplaceCompsProvider(BaseDataProvider):
    """Integrates with third-party marketplace scraping APIs (e.g., Apify).

    This provider assumes the upstream API is compliant with the relevant site
    Terms of Service and local regulations. No direct scraping is performed here;
    we simply invoke the configured API endpoint when the feature flag is enabled.
    """

    name = ApiSource.MARKETPLACE.value

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        enabled: bool,
        timeout: int = 10,
        max_results: int = 10,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.enabled = enabled
        self.timeout = timeout
        self.max_results = max_results
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def fetch_for_property(self, address: Address) -> Optional[ProviderResult]:
        if not self.enabled:
            logger.debug("Marketplace scraping disabled; skipping")
            return None

        if not self.base_url:
            logger.info("MarketplaceCompsProvider missing base_url; skipping")
            return None

        payload = {
            "line1": address.line1,
            "city": address.city,
            "state": address.state,
            "zip": address.zip,
            "limit": self.max_results,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/comps"
        response = self._request_with_retry(url, json=payload, headers=headers)
        if response is None:
            return None

        try:
            data = response.json()
        except ValueError:
            logger.warning("MarketplaceCompsProvider received non-JSON response")
            return None

        comps = data if isinstance(data, list) else data.get("results") if isinstance(data, dict) else []
        if not comps:
            return None

        normalized: List[Dict[str, Any]] = []
        rents: List[float] = []
        for comp in comps[: self.max_results]:
            if not isinstance(comp, dict):
                continue
            rent = comp.get("rent") or comp.get("price")
            try:
                rent_value = float(rent) if rent is not None else None
            except (TypeError, ValueError):
                rent_value = None

            if rent_value is not None:
                rents.append(rent_value)

            normalized.append(
                {
                    "address": comp.get("address"),
                    "beds": comp.get("beds"),
                    "baths": comp.get("baths"),
                    "rent": rent_value,
                    "distance": comp.get("distance"),
                    "days_on_market": comp.get("days_on_market"),
                }
            )

        rent_estimate = None
        if rents:
            rent_estimate = round(sum(rents) / len(rents), 2)

        patch = PropertyDataPatch(
            rent_estimate=rent_estimate,
            meta={"marketplace_comps": json.dumps(normalized) if normalized else "[]"},
            fields=["rent_estimate"] if rent_estimate is not None else [],
            raw_reference="marketplace_raw",
        )

        return ProviderResult(
            metadata=ProviderMetadata(provider_name=self.name),
            property_data=patch,
            raw_payload=normalized,
        )

    def _request_with_retry(self, url: str, *, json: Dict[str, Any], headers: Dict[str, str]) -> httpx.Response | None:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                response = httpx.post(
                    url,
                    json=json,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code == 429 and attempt < self.max_retries:
                    sleep_time = self.backoff_seconds * math.pow(2, attempt)
                    logger.info("MarketplaceCompsProvider rate limited; backing off %.2fs", sleep_time)
                    time.sleep(sleep_time)
                    attempt += 1
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                logger.warning("MarketplaceCompsProvider HTTP error %s: %s", exc.response.status_code, exc.response.text)
                return None
            except httpx.RequestError as exc:
                logger.warning("MarketplaceCompsProvider request failed: %s", exc)
                attempt += 1
        return None
