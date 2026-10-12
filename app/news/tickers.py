"""Грубая привязка заголовка к ticker. Не 100% точность, miss пишем в лог."""

import logging
from collections.abc import Mapping

from app.models import NewsEvent

log = logging.getLogger("news.tickers")

NAME_MAP: dict[str, str] = {
    "сбербанк": "SBER",
    "сбер": "SBER",
    "sberbank": "SBER",
    "sber": "SBER",
    "газпром": "GAZP",
    "gazprom": "GAZP",
    "лукойл": "LKOH",
    "lukoil": "LKOH",
    "яндекс": "YNDX",
    "yandex": "YNDX",
}


def match_tickers(
    text: str,
    names: Mapping[str, str] | None = None,
) -> list[str]:
    hay = text.casefold()
    found: list[str] = []
    for name, ticker in (names or NAME_MAP).items():
        if name.casefold() in hay and ticker not in found:
            found.append(ticker)
    return found


def bind_tickers(
    row: NewsEvent,
    names: Mapping[str, str] | None = None,
    *,
    logger: logging.Logger | None = None,
) -> NewsEvent:
    row.tickers = match_tickers(row.title, names)
    if not row.tickers:
        (logger or log).info("news ticker miss title=%s url=%s", row.title, row.url)
    return row
