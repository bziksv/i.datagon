"""Синтетические снимки фундамента для desk, когда sandbox API недоступен."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha1

from app.models import Fundamental
from app.strategy.moex_groups import all_moex_desk_tickers


def _unit(ticker: str, salt: str) -> float:
    digest = sha1(f"{ticker}:{salt}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def demo_fundamental(ticker: str, *, ts: datetime | None = None) -> Fundamental:
    name = ticker.strip().upper()
    pe = 3.5 + _unit(name, "pe") * 28.0
    pb = 0.35 + _unit(name, "pb") * 2.4
    eps = 5.0 + _unit(name, "eps") * 140.0
    roe = 0.04 + _unit(name, "roe") * 0.28
    div = 0.01 + _unit(name, "div") * 0.14
    mcap = (0.2 + _unit(name, "mcap") * 8.0) * 1_000_000_000_000.0
    return Fundamental(
        ticker=name,
        asset_uid=f"demo-{name.lower()}",
        ts=ts or datetime.now(UTC),
        pe_ratio_ttm=round(pe, 2),
        price_to_book_ttm=round(pb, 2),
        eps_ttm=round(eps, 2),
        market_capitalization=round(mcap, 2),
        raw={
            "roe": round(roe, 4),
            "free_float": round(0.25 + _unit(name, "ff") * 0.5, 4),
            "dividend_yield_daily_ttm": round(div, 4),
            "demo": True,
        },
    )


def demo_fundamentals(*, ts: datetime | None = None) -> list[Fundamental]:
    stamp = ts or datetime.now(UTC)
    return [demo_fundamental(ticker, ts=stamp) for ticker in all_moex_desk_tickers()]
