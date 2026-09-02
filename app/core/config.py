from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url


def _with_host(raw: str, host: str) -> str:
    return make_url(raw).set(host=host).render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "CoinTrace-api"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    PROD: bool = False
    DEMO: bool = False
    # True: run the API outside docker, against postgres on localhost.
    # False: run inside docker compose, against the `db` service.
    LOCAL: bool = False


    DATABASE_URL: str
    MIGRATION_DATABASE_URL: str

    USERNAME_API: str
    USERNAME_PASSWORD: str
    DEBUG: bool = False


    FRONTEND_URL: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("FRONTEND_URL", mode="before")
    @classmethod
    def handle_frontend_url(cls, raw: str | list[str]) -> list[str]:
        if not isinstance(raw, str):
            return raw
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @model_validator(mode="after")
    def handle_database_host(self) -> "Settings":
        host = "localhost" if self.LOCAL else "db"
        self.DATABASE_URL = _with_host(self.DATABASE_URL, host)
        self.MIGRATION_DATABASE_URL = _with_host(self.MIGRATION_DATABASE_URL, host)
        return self


settings = Settings()
