from pydantic import BaseSettings

class Settings(BaseSettings):
    ZILLOW_API_KEY: str | None = None
    RENTOMETER_API_KEY: str | None = None
    ATTOM_API_KEY: str | None = None
    CLOSINGCORP_API_KEY: str | None = None
    CACHE_TTL_MIN: int = 60
    
    class Config: 
        env_file = ".env"

settings = Settings() 