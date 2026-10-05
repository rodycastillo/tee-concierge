from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://tee:tee@localhost:5432/tee"
    redis_url: str = "redis://localhost:6379/0"

    whatsapp_gateway: Literal["fake", "cloud"] = "fake"
    whatsapp_api_version: str = "v21.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: SecretStr = SecretStr("")
    whatsapp_app_secret: SecretStr = SecretStr("")
    whatsapp_verify_token: SecretStr = SecretStr("change-me")

    store_name: str = "Tee Concierge"
    store_contact_phone: str = ""
    store_hours: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
