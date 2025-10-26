from __future__ import annotations
from typing import Dict, Optional

import json
import requests

from ...core.models import Address, ApiSource, PropertyData
from ...utils.logging import logger
from .base import PropertyDataProvider


class ClosingcorpProvider(PropertyDataProvider):
    """ClosingCorp closing cost estimates provider - requires API key configuration."""

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 10, fallback_rate: float = 0.03):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.fallback_rate = fallback_rate

    def fetch(self, address: Address) -> Optional[PropertyData]:
        formatted = {
            "line1": address.line1,
            "city": address.city,
            "state": address.state,
            "zip": address.zip,
        }

        if not self.base_url:
            logger.info("ClosingcorpProvider: no base URL configured, skipping fetch.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json={"property_address": formatted},
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(
                    "ClosingcorpProvider: request failed with status %s and body %s",
                    response.status_code,
                    response.text,
                )
                return None

            payload = response.json()
            meta: Dict[str, str] = {"closingcorp_raw": json.dumps(payload)}
            costs = payload.get("closing_costs") or {}
            estimate = costs.get("estimate")

            if estimate is None:
                return None
            for key in ("title", "taxes", "insurance", "lender", "recording"):
                if key in costs and costs[key] is not None:
                    meta[key] = str(costs[key])

            return PropertyData(
                address=address,
                beds=None,
                baths=None,
                sqft=None,
                lot_sqft=None,
                year_built=None,
                market_value_estimate=None,
                rent_estimate=None,
                annual_taxes=None,
                closing_cost_estimate=estimate,
                meta=meta,
                sources=[ApiSource.CLOSINGCORP],
            )

        except Exception as exc:
            logger.exception("ClosingcorpProvider: error fetching data for %s: %s", formatted, exc)
            return None