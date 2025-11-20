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
    # default_bedrooms: int | None


@dataclass(slots=True)
class EstatedConfig:
    api_key: str | None
    base_url: str
    timeout: int


@dataclass(slots=True)
class HudConfig:
    api_key: str | None
    base_url: str
    timeout: int
    cache_ttl_min: int


@dataclass(slots=True)
class MarketplaceConfig:
    enabled: bool
    api_key: str | None
    base_url: str
    timeout: int
    max_results: int
    max_retries: int
    backoff_seconds: float

@dataclass(slots=True)
class RentcastConfig:
    api_key: str | None
    base_url: str
    timeout: int


@dataclass(slots=True)
class RedfinConfig:
    api_key: str | None
    base_url: str
    timeout: int
    host: str


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = "gpt-4o-mini"

    ZILLOW_API_KEY: str | None = None
    ZILLOW_BASE_URL: str = "https://api.bridgedataoutput.com/api/v2"

    RENTOMETER_API_KEY: str | None = None
    RENTOMETER_BASE_URL: str = "https://www.rentometer.com/api/v1"
    # RENTOMETER_DEFAULT_BEDROOMS: int | None = None

    ATTOM_API_KEY: str | None = None
    ATTOM_BASE_URL: str = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"

    CLOSINGCORP_API_KEY: str | None = None
    CLOSINGCORP_BASE_URL: str | None = None

    GOOGLE_PLACES_API_KEY: str | None = None

    ESTATED_API_KEY: str | None = None
    ESTATED_BASE_URL: str = "https://apis.estated.com/v4"

    RENTCAST_API_KEY: str | None = None
    RENTCAST_BASE_URL: str = "https://api.rentcast.io/v1"

    REDFIN_API_KEY: str | None = None
    REDFIN_BASE_URL: str = "https://redfin-working-api1.p.rapidapi.com"
    REDFIN_RAPIDAPI_HOST: str = "redfin-working-api1.p.rapidapi.com"

    HUD_FMR_API_KEY: str | None = None
    HUD_FMR_BASE_URL: str = "https://www.huduser.gov/hudapi/public/fmr"
    HUD_FMR_CACHE_TTL_MIN: int = 720

    ENABLE_MARKETPLACE_SCRAPING: bool = False
    MARKETPLACE_SCRAPING_BASE_URL: str = ""
    MARKETPLACE_SCRAPING_API_KEY: str | None = None
    MARKETPLACE_SCRAPING_TIMEOUT_SEC: int = 10
    MARKETPLACE_SCRAPING_MAX_RESULTS: int = 15
    MARKETPLACE_SCRAPING_MAX_RETRIES: int = 2
    MARKETPLACE_SCRAPING_BACKOFF_SEC: float = 0.75

    DATABASE_URL: str = "sqlite:///property_underwriter.db"
    # DATABASE_URL: str = "sqlite:///./property_underwriter.db"

    CACHE_TTL_MIN: int = 60
    PROVIDER_TIMEOUT_SEC: int = 10
    USE_MOCK_PROVIDER_IF_NO_KEYS: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    # The `model_config` attribute is an instance of `pydantic.ConfigDict`.
    # It holds the following configuration settings:
    # {
    #     "env_file": ".env",
    #     "env_file_encoding": "utf-8",
    #     "extra": "ignore",
    # }


    @property
    def rentcast(self) -> RentcastConfig:
        return RentcastConfig(
            api_key=self.RENTCAST_API_KEY,
            base_url=self.RENTCAST_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
        )

    @property
    def redfin(self) -> RedfinConfig:
        return RedfinConfig(
            api_key=self.REDFIN_API_KEY,
            base_url=self.REDFIN_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
            host=self.REDFIN_RAPIDAPI_HOST,
        )

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
            # default_bedrooms=self.RENTOMETER_DEFAULT_BEDROOMS,
        )

    @property
    def estated(self) -> EstatedConfig:
        return EstatedConfig(
            api_key=self.ESTATED_API_KEY,
            base_url=self.ESTATED_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
        )

    @property
    def hud(self) -> HudConfig:
        return HudConfig(
            api_key=self.HUD_FMR_API_KEY,
            base_url=self.HUD_FMR_BASE_URL,
            timeout=self.PROVIDER_TIMEOUT_SEC,
            cache_ttl_min=self.HUD_FMR_CACHE_TTL_MIN,
        )

    @property
    def marketplace(self) -> MarketplaceConfig:
        return MarketplaceConfig(
            enabled=self.ENABLE_MARKETPLACE_SCRAPING,
            api_key=self.MARKETPLACE_SCRAPING_API_KEY,
            base_url=self.MARKETPLACE_SCRAPING_BASE_URL,
            timeout=self.MARKETPLACE_SCRAPING_TIMEOUT_SEC,
            max_results=self.MARKETPLACE_SCRAPING_MAX_RESULTS,
            max_retries=self.MARKETPLACE_SCRAPING_MAX_RETRIES,
            backoff_seconds=self.MARKETPLACE_SCRAPING_BACKOFF_SEC,
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
        "rentcast": bool(settings.RENTCAST_API_KEY),
        "redfin": bool(settings.REDFIN_API_KEY),
    }
    logger.debug("Loaded settings (provider configured flags): %s", configured)
    return settings


settings = _get_settings()
