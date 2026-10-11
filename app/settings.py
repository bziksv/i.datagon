from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    tinkoff_sandbox_token: str
    app_auth_token: str
    sandbox_deposit: int = 1_000_000


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise SettingsError(
            "Не заданы переменные окружения. Скопируйте .env.example в .env "
            "и заполните DATABASE_URL, TINKOFF_SANDBOX_TOKEN, APP_AUTH_TOKEN."
        ) from exc
