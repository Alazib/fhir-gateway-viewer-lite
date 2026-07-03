from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FHIR Mini-Gateway API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "development", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"
    )

    auth_jwt_secret: str | None = None
    auth_jwt_issuer: str = "fhir-gateway-local"
    auth_jwt_audience: str = "fhir-gateway-api"
    auth_jwt_algorithm: Literal["HS256"] = "HS256"

    model_config = SettingsConfigDict(
        env_prefix="FHIR_GATEWAY_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
