from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.logging import logger

class Settings(BaseSettings):
    ZILLOW_API_KEY: str | None = None
    ZILLOW_BASE_URL: str = "https://api.bridgedataoutput.com/api/v2"

    RENTOMETER_API_KEY: str | None = None
    RENTOMETER_BASE_URL: str = "https://www.rentometer.com/api/v1"
    RENTOMETER_DEFAULT_BEDROOMS: int | None = None

    ATTOM_API_KEY: str | None = None
    ATTOM_BASE_URL: str = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"

    CLOSINGCORP_API_KEY: str | None = None
    CLOSINGCORP_BASE_URL: str | None = None

    CACHE_TTL_MIN: int = 60
    PROVIDER_TIMEOUT_SEC: int = 10
    USE_MOCK_PROVIDER_IF_NO_KEYS: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

logger.info(f"Settings: {Settings()}")
settings = Settings()