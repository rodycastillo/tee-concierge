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

    # The business is described by the menu file; these override its values when set, so real
    # contact data never has to be committed.
    menu_config: str = "examples/tshirt-store/menu.yaml"
    store_name: str = ""
    store_contact_phone: str = ""
    store_hours: str = ""

    admin_api_key: SecretStr = SecretStr("")  # empty disables the admin API
    rate_limit_per_minute: int = 20  # inbound messages per customer
    metrics_port: int = 9100  # worker Prometheus endpoint


@lru_cache
def get_settings() -> Settings:
    return Settings()
