import pytest

from src.core.models import Address
from src.services import google_places


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP error")

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def reset_google_places_cache():
    google_places.get_place_details.cache_clear()
    yield
    google_places.get_place_details.cache_clear()


def test_parse_address_components_complete():
    components = [
        {"long_name": "123", "types": ["street_number"]},
        {"long_name": "Main St", "types": ["route"]},
        {"long_name": "Springfield", "types": ["locality"]},
        {"long_name": "IL", "types": ["administrative_area_level_1"]},
        {"long_name": "62704", "types": ["postal_code"]},
    ]

    result = google_places._parse_address_components(components)

    assert result == Address(line1="123 Main St", city="Springfield", state="IL", zip="62704")


def test_parse_address_components_incomplete(caplog):
    caplog.set_level("WARNING")
    components = [
        {"long_name": "123", "types": ["street_number"]},
        {"long_name": "Main St", "types": ["route"]},
    ]

    result = google_places._parse_address_components(components)

    assert result is None
    assert "Incomplete address components" in caplog.text


def test_is_enabled_false_logs_debug(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", None)

    assert google_places._is_enabled() is False
    assert "autocomplete disabled" in caplog.text


def test_is_enabled_true(monkeypatch):
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")

    assert google_places._is_enabled() is True


def test_get_place_suggestions_success(monkeypatch):
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")
    monkeypatch.setattr(google_places.settings, "PROVIDER_TIMEOUT_SEC", 3)

    calls = []

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        assert url == google_places.AUTOCOMPLETE_URL
        return DummyResponse(
            {
                "status": "OK",
                "predictions": [
                    {"description": "Alpha", "place_id": "pid1"},
                    {"description": "Beta", "place_id": "pid2"},
                    {"description": "No Id"},
                ],
            }
        )

    monkeypatch.setattr(google_places.requests, "get", fake_get)

    result = google_places.get_place_suggestions("main", session_token="token-1", country="us")

    assert result == [
        {"description": "Alpha", "place_id": "pid1"},
        {"description": "Beta", "place_id": "pid2"},
    ]
    assert calls
    assert calls[0][1]["sessiontoken"] == "token-1"
    assert calls[0][1]["components"] == "country:us"


def test_get_place_suggestions_non_ok_status(monkeypatch, caplog):
    caplog.set_level("WARNING")
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")
    monkeypatch.setattr(google_places.requests, "get", lambda *args, **kwargs: DummyResponse({"status": "ZERO_RESULTS"}))

    result = google_places.get_place_suggestions("main")

    assert result == []
    assert "returned status ZERO_RESULTS" in caplog.text


def test_get_place_suggestions_exception(monkeypatch, caplog):
    caplog.set_level("ERROR")
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")

    def fake_get(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(google_places.requests, "get", fake_get)

    result = google_places.get_place_suggestions("main")

    assert result == []
    assert "Google Places autocomplete failed" in caplog.text


def test_get_place_details_success(monkeypatch):
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")
    monkeypatch.setattr(google_places.settings, "PROVIDER_TIMEOUT_SEC", 5)

    def fake_get(url, params, timeout):
        assert url == google_places.DETAILS_URL
        return DummyResponse(
            {
                "status": "OK",
                "result": {
                    "address_components": [
                        {"long_name": "1600", "types": ["street_number"]},
                        {"long_name": "Pennsylvania Ave NW", "types": ["route"]},
                        {"long_name": "Washington", "types": ["locality"]},
                        {"short_name": "DC", "types": ["administrative_area_level_1"]},
                        {"long_name": "20500", "types": ["postal_code"]},
                    ]
                },
            }
        )

    monkeypatch.setattr(google_places.requests, "get", fake_get)

    result = google_places.get_place_details("pid")

    assert result == Address(line1="1600 Pennsylvania Ave NW", city="Washington", state="DC", zip="20500")


def test_get_place_details_error(monkeypatch, caplog):
    caplog.set_level("ERROR")
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")
    monkeypatch.setattr(google_places.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    result = google_places.get_place_details("pid")

    assert result is None
    assert "Google Places details lookup failed" in caplog.text


def test_get_place_details_cache(monkeypatch):
    monkeypatch.setattr(google_places.settings, "GOOGLE_PLACES_API_KEY", "token")

    call_count = {"count": 0}

    def fake_get(url, params, timeout):
        call_count["count"] += 1
        return DummyResponse({"status": "OK", "result": {"address_components": []}})

    monkeypatch.setattr(google_places.requests, "get", fake_get)

    assert google_places.get_place_details("pid") is None
    assert google_places.get_place_details("pid") is None
    assert call_count["count"] == 1
