from dataclasses import dataclass
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.logging import logger


@dataclass(slots=True)
class ZillowConfig:
    api_key: str | None
    base_url: str
    timeout: int


@dataclass(slots=True)
class RentometerConfig:
    api_key: str | None
    base_url: str
    timeout: int
    default_bedrooms: int | None


@dataclass(slots=True)
class EstatedConfig:
    api_key: str | None
    base_url: str
    timeout: int


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

    GOOGLE_PLACES_API_KEY: str | None = None

    ESTATED_API_KEY: str | None = None
    ESTATED_BASE_URL: str = "https://apis.estated.com/v4"

    DATABASE_URL: str = "sqlite:///property_underwriter.db"

    CACHE_TTL_MIN: int = 60
    PROVIDER_TIMEOUT_SEC: int = 10
    USE_MOCK_PROVIDER_IF_NO_KEYS: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def zillow(self) -> ZillowConfig:
        return ZillowConfig(
            api_key=self.ZILLOW_API_KEY,
            base_url=self.ZILLOW_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
        )

    @property
    def rentometer(self) -> RentometerConfig:
        return RentometerConfig(
            api_key=self.RENTOMETER_API_KEY,
            base_url=self.RENTOMETER_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
            default_bedrooms=self.RENTOMETER_DEFAULT_BEDROOMS,
        )

    @property
    def estated(self) -> EstatedConfig:
        return EstatedConfig(
            api_key=self.ESTATED_API_KEY,
            base_url=self.ESTATED_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
        )


@lru_cache(maxsize=1)
def _get_settings() -> Settings:
    settings = Settings()
    configured = {
        "zillow": bool(settings.ZILLOW_API_KEY),
        "rentometer": bool(settings.RENTOMETER_API_KEY),
        "attom": bool(settings.ATTOM_API_KEY),
        "closingcorp": bool(settings.CLOSINGCORP_API_KEY),
        "estated": bool(settings.ESTATED_API_KEY),
    }
    logger.debug("Loaded settings (provider configured flags): %s", configured)
    return settings


settings = _get_settings()
