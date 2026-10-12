import inspect

import pytest

from app.ops import telegram
from app.ops.telegram import (
    ALLOWED_KINDS,
    TelegramKindError,
    alert_drift,
    alert_kill,
    notify,
    send_telegram,
    telegram_enabled,
)
from app.settings import Settings


def test_telegram_off_by_default(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "t")
    monkeypatch.setenv("APP_AUTH_TOKEN", "a")
    monkeypatch.setenv("TELEGRAM_ENABLED", "0")
    assert Settings().telegram_enabled is False
    assert telegram_enabled() is False
    sent: list[str] = []
    assert alert_kill(True, send=sent.append) is None
    assert alert_drift("ALERT drift", send=sent.append) is None
    assert sent == []


def test_only_kill_and_drift_when_on() -> None:
    sent: list[str] = []
    assert alert_kill(True, enabled=True, send=sent.append) == "ALERT kill=True"
    assert alert_drift("ALERT drift x", enabled=True, send=sent.append) == "ALERT drift x"
    assert ALLOWED_KINDS == {"kill", "drift"}
    with pytest.raises(TelegramKindError):
        notify("order", "buy", enabled=True, send=sent.append)
    assert "buy" not in sent


def test_telegram_module_is_not_trading() -> None:
    source = inspect.getsource(telegram)
    assert "place_order" not in source
    assert "propose_order" not in source
    assert "post_order" not in source
    assert "OrderRequest" not in source
    assert 'method="POST"' in inspect.getsource(send_telegram)
    assert "chat_id" in source
