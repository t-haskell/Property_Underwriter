from __future__ import annotations
from typing import Dict, Optional

import json
import requests

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class AttomProvider(PropertyDataProvider):
    """ATTOM property and tax data provider - requires API key configuration."""

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 10):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.gateway.attomdata.com/propertyapi/v1.0.0").rstrip("/")
        self.timeout = timeout

    def fetch(self, address: Address) -> Optional[PropertyData]:
        formatted = f"{address.line1}, {address.city}, {address.state} {address.zip}"
        headers = {
            "apikey": self.api_key,
        }
        params = {"address": formatted}

        try:
            url = f"{self.base_url}/property/basicprofile"
            logger.info("AttomProvider: Making request to %s with params %s", url, params)
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(
                    "AttomProvider: request failed with status %s and body %s",
                    response.status_code,
                    response.text,
                )
                return None

            payload = response.json()
            meta: Dict[str, str] = {"attom_raw": json.dumps(payload)}
            properties = payload.get("property") or []
            if not properties:
                return None

            record = properties[0]
            building = record.get("building", {})
            rooms = building.get("rooms", {})
            size = building.get("size", {})
            lot = record.get("lot", {})
            summary = record.get("summary", {})
            assessment = record.get("assessment", {}) or {}
            market = assessment.get("market") or {}
            tax = assessment.get("tax") or {}
            legal1 = summary.get("legal1")
            if legal1 is not None:
                meta["legal1"] = str(legal1)
            
            identifier = record.get("identifier", {})
            parcelid = identifier.get("apn")    # APN is the parcel ID
            if parcelid is not None:
                meta["parcelid"] = str(parcelid)
            
            fipscode = identifier.get("fips")
            if fipscode is not None:
                meta["fipscode"] = str(fipscode)

            return PropertyData(
                address=address,
                beds=rooms.get("beds"),
                baths=rooms.get("bathsTotal"),
                sqft=size.get("universalSize"),
                lot_sqft=lot.get("lotSize2"),
                year_built=summary.get("yearBuilt"),
                market_value_estimate=market.get("mktTtlValue"),
                rent_estimate=None,
                annual_taxes=tax.get("taxAmt"),
                closing_cost_estimate=None,
                meta=meta,
                sources=[ApiSource.ATTOM],
            )

        except Exception as exc:
            logger.exception("AttomProvider: error fetching data for %s: %s", formatted, exc)
            return None