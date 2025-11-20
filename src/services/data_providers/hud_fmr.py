from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Dict, Optional

import httpx

from ...core.models import Address, ApiSource
from ...utils.logging import logger
from .base import BaseDataProvider
from .models import AreaIdentifier, AreaRentBenchmark, ProviderMetadata, ProviderResult


class HudFmrProvider(BaseDataProvider):
    """Fetch HUD Fair Market Rent benchmarks.

    Uses the public HUD FMR endpoint (or a compatible open-data source) to obtain
    area-level rent benchmarks by bedroom count. Requests are cached in-memory to
    minimise repeat lookups for the same ZIP/metro.
    """

    name = ApiSource.HUD.value

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 10,
        cache_ttl_min: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.cache_ttl_min = cache_ttl_min
        self._cache: Dict[str, tuple[datetime, ProviderResult]] = {}

    def fetch_for_property(self, address: Address) -> Optional[ProviderResult]:
        area = AreaIdentifier(zip=address.zip, state=address.state)
        return self.fetch_for_area(area)

    def fetch_for_area(self, area_identifier: AreaIdentifier) -> Optional[ProviderResult]:
        zip_code = area_identifier.zip
        if not zip_code:
            logger.info("HudFmrProvider requires a ZIP code; skipping")
            return None

        cached = self._cached_response(zip_code)
        if cached:
            return cached

        params: Dict[str, str] = {"zip": zip_code}
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/fmr" if not self.base_url.endswith("/fmr") else self.base_url
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("HUD FMR HTTP error %s: %s", exc.response.status_code, exc.response.text)
            return None
        except httpx.RequestError as exc:
            logger.warning("HUD FMR request failed: %s", exc)
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning("HUD FMR returned non-JSON payload for %s", zip_code)
            return None

        benchmarks = self._parse_benchmarks(payload, area_identifier)
        if not benchmarks:
            return None

        result = ProviderResult(
            metadata=ProviderMetadata(provider_name=self.name),
            area_rent_benchmarks=benchmarks,
            raw_payload=payload,
        )
        self._cache_result(zip_code, result)
        return result

    def _parse_benchmarks(self, payload: Dict, area: AreaIdentifier) -> list[AreaRentBenchmark]:
        fmr = payload.get("fmr") or payload.get("fmr_values") or {}
        if not isinstance(fmr, dict):
            return []

        year = None
        raw_year = payload.get("year")
        if isinstance(raw_year, (int, float, str)):
            try:
                year = int(raw_year)
            except (TypeError, ValueError):
                year = None

        benchmarks: list[AreaRentBenchmark] = []
        for bedroom_key, amount in fmr.items():
            try:
                rent = float(amount)
            except (TypeError, ValueError):
                continue

            try:
                bedroom_count = int(bedroom_key)
            except (TypeError, ValueError):
                bedroom_count = None

            benchmarks.append(
                AreaRentBenchmark(
                    area=area,
                    bedroom_count=bedroom_count,
                    rent=rent,
                    currency="USD",
                    year=year,
                )
            )
        return benchmarks

    def _cached_response(self, zip_code: str) -> Optional[ProviderResult]:
        entry = getattr(self, "_cache", {}).get(zip_code)
        if not entry:
            return None

        expires_at, result = entry
        if datetime.now(UTC) > expires_at:
            getattr(self, "_cache", {}).pop(zip_code, None)
            return None
        return result

    def _cache_result(self, zip_code: str, result: ProviderResult) -> None:
        expiry = datetime.now(UTC) + timedelta(minutes=self.cache_ttl_min)
        if not hasattr(self, "_cache"):
            self._cache = {}
        self._cache[zip_code] = (expiry, result)

