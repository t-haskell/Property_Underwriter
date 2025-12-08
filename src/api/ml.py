"""Lightweight ML-inspired endpoints with local fallback logic."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/ml", tags=["ml"])


class PropertyQARequest(BaseModel):
    question: str
    address: Optional[str] = None
    year_built: Optional[int] = None
    occupancy: Optional[str] = None
    known_hazards: Optional[str] = None


class PropertyQAResponse(BaseModel):
    answer: str
    risk_score: str
    debug: Optional[Dict[str, Any]] = None


def simple_risk_estimate(context: Dict[str, Any]) -> str:
    """Very simple rule-based risk score for demonstration purposes."""

    score = 0
    year_built = context.get("year_built")
    hazards = (context.get("known_hazards") or "").lower()
    occupancy = (context.get("occupancy") or "").lower()

    if year_built is not None and year_built < 1950:
        score += 2
    if "flood" in hazards or "river" in hazards:
        score += 3
    if "industrial" in occupancy or "commercial" in occupancy:
        score += 1

    if score <= 1:
        return "low"
    if score <= 3:
        return "medium"
    return "high"


def local_answer(question: str, context: Dict[str, Any]) -> str:
    """Deterministic answers for common questions."""

    normalized_question = (question or "").lower()

    if "flood" in normalized_question:
        hazards = (context.get("known_hazards") or "").lower()
        if hazards and "flood" in hazards:
            return (
                "Based on known hazards this area has flood risk. "
                "Consider flood insurance and mitigation steps such as grading or elevation."
            )
        return (
            "Check FEMA flood maps for the address. If it is near rivers or low elevation, "
            "flood risk could be higher."
        )

    if "age" in normalized_question or "year" in normalized_question or "built" in normalized_question:
        year_built = context.get("year_built")
        return f"Property year built: {year_built}" if year_built else "Year built not provided."

    return (
        "I can help identify potential risks. Provide more context such as year built, "
        "occupancy, or known hazards."
    )


@router.post("/property_qa", response_model=PropertyQAResponse)
def property_qa(payload: PropertyQARequest) -> PropertyQAResponse:
    """Property Q&A endpoint with optional remote inference and local fallback."""

    context: Dict[str, Any] = {
        "address": payload.address,
        "year_built": payload.year_built,
        "occupancy": payload.occupancy,
        "known_hazards": payload.known_hazards,
    }

    ml_url = os.getenv("ML_API_URL")
    ml_key = os.getenv("ML_API_KEY")
    remote_error: Optional[str] = None

    if ml_url and ml_key:
        try:
            response = requests.post(
                ml_url,
                json={"question": payload.question, "context": context},
                headers={"Authorization": f"Bearer {ml_key}"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return PropertyQAResponse(
                answer=data.get("answer", ""),
                risk_score=data.get("risk_score", "unknown"),
                debug={"remote": True},
            )
        except Exception as exc:  # pragma: no cover - fallback to local
            remote_error = str(exc)

    answer = local_answer(payload.question, context)
    risk = simple_risk_estimate(context)
    debug = {"remote_attempted": bool(ml_url and ml_key), "remote_error": remote_error}

    return PropertyQAResponse(answer=answer, risk_score=risk, debug=debug)
