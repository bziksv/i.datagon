"""Optional Telegram: только kill/drift. По умолчанию выключен. Не торговля."""

import os
from collections.abc import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ALLOWED_KINDS = frozenset({"kill", "drift"})


class TelegramKindError(ValueError):
    pass


def telegram_enabled(*, enabled: bool | None = None) -> bool:
    flag = os.environ.get("TELEGRAM_ENABLED", "0") if enabled is None else enabled
    return flag in (True, "1", "true", "True")


def notify(
    kind: str,
    text: str,
    *,
    send: Callable[[str], str] | None = None,
    enabled: bool | None = None,
) -> str | None:
    if kind not in ALLOWED_KINDS:
        raise TelegramKindError(f"telegram kind {kind} is not kill/drift")
    if not telegram_enabled(enabled=enabled):
        return None
    if send is None:
        return None
    send(text)
    return text


def alert_kill(killed: bool, **kwargs) -> str | None:
    return notify("kill", f"ALERT kill={killed}", **kwargs)


def alert_drift(message: str | None, **kwargs) -> str | None:
    if not message:
        return None
    return notify("drift", message, **kwargs)


def send_telegram(text: str) -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    body = urlencode({"chat_id": chat, "text": text}).encode()
    req = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urlopen(req, timeout=5) as resp:  # noqa: S310
        return resp.read().decode()
