from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    tinkoff_sandbox_token: str
    tinkoff_live: bool = False
    app_auth_token: str
    sandbox_deposit: int = 1_000_000
    liquidity_min_turnover: int = 10_000_000
    liquidity_max_spread_bps: int = 50
    universe_max: int = 30
    universe_fundamentals: bool = False
    sma_fast: int = 5
    sma_slow: int = 20
    name_share: float = 0.10
    sleeve_share: float = 0.40
    daily_loss_pct: float = 0.03
    stop_pct: float = 0.05
    agent_interval_min: int = 15
    agents_enabled: bool = False
    news_rss_url: str = ""
    cabin_rate_per_min: int = 120
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise SettingsError(
            "Не заданы переменные окружения. Скопируйте .env.example в .env "
            "и заполните DATABASE_URL, TINKOFF_SANDBOX_TOKEN, APP_AUTH_TOKEN."
        ) from exc
