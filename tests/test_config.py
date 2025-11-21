from src.utils.config import DEFAULT_ALLOWED_ORIGINS, Settings


def test_api_allowed_origins_defaults_to_known_values():
    settings = Settings()

    assert settings.api_allowed_origins == DEFAULT_ALLOWED_ORIGINS


def test_api_allowed_origins_parses_comma_separated_values():
    settings = Settings(API_ALLOWED_ORIGINS=" https://example.com ,http://localhost:4000/ , https://example.com ")

    assert settings.api_allowed_origins == ["https://example.com", "http://localhost:4000"]
