from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class EstatedProvider(PropertyDataProvider):
    """Property data provider that integrates with the Estated API."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int = 10,
    ) -> None:
        if not api_key:
            raise ValueError("EstatedProvider requires a non-empty API key")

        self.api_key = api_key
        self.base_url = (base_url or "https://apis.estated.com/v4").rstrip("/")
        self.timeout = timeout

    def fetch(self, address: Address) -> Optional[PropertyData]:
        params = self._build_params(address)
        response = self._request("/property", params=params)
        if response is None:
            return None

        payload = self._parse_response(response)
        if payload is None:
            return None

        property_payload = payload.get("property") or payload
        if not isinstance(property_payload, dict):
            logger.error(
                "EstatedProvider: unexpected property payload type %s", type(property_payload)
            )
            return None

        structure = property_payload.get("structure")
        if not isinstance(structure, dict):
            structure = {}

        land = property_payload.get("land")
        if not isinstance(land, dict):
            land = {}

        valuation = property_payload.get("valuation")
        if not isinstance(valuation, dict):
            valuation = {}

        tax_info = property_payload.get("tax")
        if not isinstance(tax_info, dict):
            tax_info = {}

        beds = self._coerce_float(
            structure.get("beds")
            or structure.get("bedrooms")
            or structure.get("total_bedrooms")
        )
        baths = self._coerce_float(
            structure.get("baths")
            or structure.get("bathrooms")
            or structure.get("total_bathrooms")
        )
        sqft = self._coerce_int(
            structure.get("total_square_feet")
            or structure.get("total_sq_ft")
            or structure.get("total_finished_square_feet")
            or structure.get("total_finished_sq_ft")
            or structure.get("gross_living_area")
        )
        lot_sqft = self._coerce_int(
            land.get("lot_square_feet")
            or land.get("lot_sq_ft")
            or land.get("lot_size_sq_ft")
        )
        year_built = self._coerce_int(structure.get("year_built"))

        market_value = self._extract_market_value(valuation)
        rent_estimate = self._extract_rent_estimate(valuation)
        annual_taxes = self._extract_tax_amount(tax_info, valuation)

        meta: Dict[str, str] = {}
        identifier = property_payload.get("identifier") or property_payload.get("id")
        if identifier:
            meta["estated_identifier"] = str(identifier)

        market_section = valuation.get("market") or {}
        market_value_section: Dict[str, Any] = {}
        value_section = market_section.get("value")
        if isinstance(value_section, dict):
            market_value_section = value_section
        
        valuation_dates = [
            valuation.get("as_of"),
            valuation.get("updated"),
            market_section.get("updated"),
        ]
        for key, value in (
            (
                "valuation_low",
                self._coerce_float(market_section.get("low") or market_value_section.get("low")),
            ),
            (
                "valuation_high",
                self._coerce_float(market_section.get("high") or market_value_section.get("high")),
            ),
            (
                "valuation_confidence",
                self._coerce_float(market_section.get("confidence") or market_value_section.get("confidence")),
            ),
            ("valuation_date", next((str(item) for item in valuation_dates if item), None)),
        ):
            if value is not None:
                meta[key] = str(value)

        rent_section = valuation.get("rent") or {}
        if rent_section.get("updated"):
            meta["rent_estimate_date"] = str(rent_section.get("updated"))

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
            sources=[ApiSource.ESTATED],
        )

    def _request(self, path: str, *, params: Dict[str, str]) -> Optional[httpx.Response]:
        url = f"{self.base_url}{path}"
        query = {"token": self.api_key, **params}
        try:
            response = httpx.get(url, params=query, timeout=self.timeout)
        except httpx.HTTPError as exc:
            logger.warning("EstatedProvider: HTTP error calling %s: %s", url, exc)
            return None

        if response.status_code == 429:
            logger.warning("EstatedProvider: rate limited when calling %s", url)
            return None

        if response.is_error:
            logger.warning(
                "EstatedProvider: request to %s failed with status %s and body %s",
                url,
                response.status_code,
                response.text,
            )
            return None

        return response

    def _parse_response(self, response: httpx.Response) -> Optional[dict]:
        try:
            payload = response.json()
        except ValueError:
            logger.error("EstatedProvider: failed to decode JSON response")
            return None

        status = str(payload.get("status", "")).lower()
        if status and status not in {"success", "ok"}:
            logger.info("EstatedProvider: API returned status '%s'", status)
            return None

        data = payload.get("data")
        if isinstance(data, dict):
            return data

        logger.error("EstatedProvider: unexpected data payload type %s", type(data))
        return None

    @staticmethod
    def _build_params(address: Address) -> Dict[str, str]:
        return {
            "address": address.line1,
            "city": address.city,
            "state": address.state,
            "postal_code": address.zip,
        }

    @staticmethod
    def _coerce_float(value) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_int(value) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number:
            return None
        return int(number)

    def _extract_market_value(self, valuation: dict) -> Optional[float]:
        market = valuation.get("market") or {}
        value_section = market.get("value")
        if isinstance(value_section, dict):
            for key in ("estimate", "value", "amount"):
                value = value_section.get(key)
                result = self._coerce_float(value)
                if result is not None:
                    return result
        for key in ("estimate", "value", "amount"):
            result = self._coerce_float(market.get(key) or valuation.get(key))
            if result is not None:
                return result
        base_value = valuation.get("value")
        if isinstance(base_value, dict):
            for key in ("estimate", "value", "amount"):
                result = self._coerce_float(base_value.get(key))
                if result is not None:
                    return result
        return None

    def _extract_rent_estimate(self, valuation: dict) -> Optional[float]:
        rent = valuation.get("rent") or {}
        if isinstance(rent, dict):
            for key in ("estimate", "value", "amount"):
                result = self._coerce_float(rent.get(key))
                if result is not None:
                    return result
        return None

    def _extract_tax_amount(self, tax_info: dict, valuation: dict) -> Optional[float]:
        if isinstance(tax_info, dict):
            for key in ("amount", "annual", "value"):
                result = self._coerce_float(tax_info.get(key))
                if result is not None:
                    return result
        tax_section = valuation.get("tax") or {}
        if isinstance(tax_section, dict):
            for key in ("amount", "annual", "value"):
                result = self._coerce_float(tax_section.get(key))
                if result is not None:
                    return result
        return None
