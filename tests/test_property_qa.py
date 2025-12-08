from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_property_qa_local_fallback(monkeypatch) -> None:
    monkeypatch.delenv("ML_API_URL", raising=False)
    monkeypatch.delenv("ML_API_KEY", raising=False)
    payload = {
        "question": "Is this property flood prone?",
        "address": "123 River St",
        "year_built": 1940,
        "occupancy": "residential",
        "known_hazards": "near river, occasional flood",
    }

    response = client.post("/api/ml/property_qa", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] in {"medium", "high", "low"}
    assert "answer" in data
    assert data.get("debug", {}).get("remote_attempted") is False
