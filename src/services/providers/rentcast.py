from __future__ import annotations

from typing import Any, Dict, Optional
import json

import httpx

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class RentcastProvider(PropertyDataProvider):
    """Rentcast property data provider - requires API key configuration."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int = 10,
    ) -> None:
        if not api_key:
            raise ValueError("RentcastProvider requires a non-empty API key")

        self.api_key = api_key
        self.base_url = (base_url or "https://api.rentcast.io/v1").rstrip("/")
        self.timeout = timeout

    def fetch(self, address: Address) -> Optional[PropertyData]:
        params = {
            "address": address.line1,
            "city": address.city,
            "state": address.state,
            "zipCode": address.zip,
        }

        response = self._request("/properties", params=params)
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.error(
                "RentcastProvider: failed to decode response JSON for %s, %s, %s %s",
                address.line1, address.city, address.state, address.zip
            )
            return None

        # Rentcast returns a list of properties at the top level
        if not isinstance(payload, list) or not payload:
            logger.info(
                "RentcastProvider: no properties found for %s, %s, %s %s",
                address.line1, address.city, address.state, address.zip
            )
            return None

        property_data_payload = payload[0]
        if not isinstance(property_data_payload, dict):
            logger.error(
                "RentcastProvider: unexpected property payload type %s", type(property_data_payload)
            )
            return None

        # Get the most recent tax assessment for market value estimate
        tax_assessments = property_data_payload.get("taxAssessments") or {}
        most_recent_assessment = None
        if isinstance(tax_assessments, dict):
            years = [y for y in tax_assessments.keys() if isinstance(y, str) and y.isdigit()]
            if years:
                most_recent_year = max(years, key=int)
                most_recent_assessment = tax_assessments.get(most_recent_year)
        
        # Get the most recent property taxes
        property_taxes = property_data_payload.get("propertyTaxes") or {}
        most_recent_taxes = None
        if isinstance(property_taxes, dict):
            years = [y for y in property_taxes.keys() if isinstance(y, str) and y.isdigit()]
            if years:
                most_recent_year = max(years, key=int)
                most_recent_taxes = property_taxes.get(most_recent_year)

        # Build metadata from available fields
        meta: Dict[str, str] = {}
        # Include the FULL raw provider response as a JSON string for frontend debugging/inspection
        try:
            meta["rentcast_raw"] = json.dumps(payload)
        except Exception:
            # Best-effort: store stringified payload
            meta["rentcast_raw"] = str(payload)
        for key in ("id", "propertyType", "county", "subdivision"):
            value = property_data_payload.get(key)
            if value is not None:
                meta[key] = str(value)
        
        # Add last sale information
        last_sale_price = property_data_payload.get("lastSalePrice")
        if last_sale_price is not None:
            meta["lastSalePrice"] = str(last_sale_price)
        
        last_sale_date = property_data_payload.get("lastSaleDate")
        if last_sale_date is not None:
            meta["lastSaleDate"] = str(last_sale_date)

        # Get HOA fee if available
        hoa = property_data_payload.get("hoa") or {}
        if isinstance(hoa, dict):
            hoa_fee = hoa.get("fee")
            if hoa_fee is not None:
                meta["hoaFee"] = str(hoa_fee)

        return PropertyData(
            address=address,
            beds=property_data_payload.get("bedrooms"),
            baths=property_data_payload.get("bathrooms"),
            sqft=property_data_payload.get("squareFootage"),
            lot_sqft=property_data_payload.get("lotSize"),
            year_built=property_data_payload.get("yearBuilt"),
            market_value_estimate=most_recent_assessment.get("value") if isinstance(most_recent_assessment, dict) else None,
            rent_estimate=None,  # Rentcast properties endpoint does not provide rent estimates
            annual_taxes=most_recent_taxes.get("total") if isinstance(most_recent_taxes, dict) else None,
            closing_cost_estimate=None,  # Rentcast does not provide this directly
            meta=meta,
            sources=[ApiSource.RENTCAST],
        )

    def _request(self, path: str, params: Dict[str, Any]) -> Optional[httpx.Response]:
        url = f"{self.base_url}{path}"
        headers = {"X-Api-Key": self.api_key, 
                "accept": "application/json"}

        try:
            ap1: str | None = None   # address
            ap2: str | None = None   # city
            ap3: str | None = None   # state
            ap4: str | None = None   # zip code
            address_parts = [p for p in (ap1, ap2, ap3, ap4) if p]
            rest_url = "%20".join(address_parts)
            logger.info("RentcastProvider: rest_url for %s: %s", url, rest_url)
            response = httpx.get(url + "?address=" + rest_url, headers=headers, timeout=self.timeout)
            # logger.info("RentcastProvider: response for %s: %s", url, response.json())
            response.raise_for_status()
            return response 
        except httpx.HTTPStatusError as e:
            logger.error(
                "RentcastProvider: HTTP error for %s: %s - %s",
                url, e.response.status_code, e.response.text
            )
        except httpx.RequestError as e:
            logger.error("RentcastProvider: request error for %s: %s", url, e)
        return None
