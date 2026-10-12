"""Дневные свечи Yahoo Finance для desk-бэктеста (S&P 500 и др.)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.broker.port import CandleBar

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Ликвидный desk-набор крупных имён S&P 500 (не весь индекс).
DEFAULT_SP500_DESK = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "BRK-B",
    "JPM",
    "V",
    "UNH",
    "XOM",
    "JNJ",
    "PG",
    "MA",
    "HD",
    "AVGO",
    "COST",
    "LLY",
    "TSLA",
    "BAC",
    "NFLX",
    "ORCL",
    "AMD",
    "KO",
    "WMT",
)


def _request_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; i.datagon/desk-candles)",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=45) as response:  # noqa: S310
        return json.loads(response.read())


def fetch_yahoo_daily(
    ticker: str,
    *,
    from_day: date,
    till_day: date,
    request_json: Callable[[str], dict] = _request_json,
) -> list[CandleBar]:
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("ticker")
    period1 = int(datetime(from_day.year, from_day.month, from_day.day, tzinfo=UTC).timestamp())
    period2 = int(
        datetime(till_day.year, till_day.month, till_day.day, 23, 59, 59, tzinfo=UTC).timestamp()
    )
    query = urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
    )
    encoded = quote(symbol, safe="-.")
    url = f"{YAHOO_CHART_URL.format(symbol=encoded)}?{query}"
    payload = request_json(url)
    chart = (payload.get("chart") or {}).get("result") or []
    if not chart:
        error = (payload.get("chart") or {}).get("error")
        raise ValueError(f"yahoo empty: {symbol}" + (f" ({error})" if error else ""))
    block = chart[0]
    timestamps = list(block.get("timestamp") or [])
    ohlcv = ((block.get("indicators") or {}).get("quote") or [{}])[0]
    opens = list(ohlcv.get("open") or [])
    highs = list(ohlcv.get("high") or [])
    lows = list(ohlcv.get("low") or [])
    closes = list(ohlcv.get("close") or [])
    volumes = list(ohlcv.get("volume") or [])
    bars: list[CandleBar] = []
    for index, raw_ts in enumerate(timestamps):
        try:
            o = opens[index]
            h = highs[index]
            low = lows[index]
            c = closes[index]
            v = volumes[index] if index < len(volumes) else 0
        except IndexError:
            continue
        if o is None or h is None or low is None or c is None:
            continue
        bars.append(
            CandleBar(
                ts=datetime.fromtimestamp(int(raw_ts), tz=UTC),
                o=Decimal(str(o)),
                h=Decimal(str(h)),
                low=Decimal(str(low)),
                c=Decimal(str(c)),
                v=Decimal(str(v or 0)),
            )
        )
    bars.sort(key=lambda bar: bar.ts)
    return bars


def write_yahoo_csv(path: Path, bars: list[CandleBar]) -> Path:
    from app.broker.moex_candles import write_candle_csv

    return write_candle_csv(path, bars)
