"""Окно доходности T−1…T+N по свечам → строка news_studies."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.broker.port import CandleBar
from app.models import NewsEvent, NewsStudy

DEFAULT_HORIZON_N = 3


def window_bars(
    bars: Sequence[CandleBar],
    news_ts: datetime,
    *,
    n: int = DEFAULT_HORIZON_N,
) -> tuple[CandleBar, CandleBar] | None:
    ordered = sorted(bars, key=lambda row: row.ts)
    t_idx = next((i for i, row in enumerate(ordered) if row.ts >= news_ts), None)
    if t_idx is None or t_idx == 0:
        return None
    plus = t_idx + n
    if plus >= len(ordered):
        return None
    return ordered[t_idx - 1], ordered[plus]


def study_return(left: CandleBar, right: CandleBar) -> Decimal:
    if left.c == 0:
        return Decimal("0")
    return (right.c - left.c) / left.c


def make_study(
    event: NewsEvent,
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    n: int = DEFAULT_HORIZON_N,
) -> NewsStudy | None:
    pair = window_bars(bars, event.ts, n=n)
    if pair is None:
        return None
    left, right = pair
    ret = study_return(left, right)
    return NewsStudy(
        id=uuid4(),
        news_event_id=event.id,
        ticker=ticker,
        horizon_n=n,
        t_minus_ts=left.ts,
        t_plus_ts=right.ts,
        ret=ret,
        payload={
            "t_minus_c": str(left.c),
            "t_plus_c": str(right.c),
            "title": event.title,
        },
    )


def run_news_studies(
    events: Sequence[NewsEvent],
    bars_by_ticker: Mapping[str, Sequence[CandleBar]],
    *,
    n: int = DEFAULT_HORIZON_N,
) -> list[NewsStudy]:
    rows: list[NewsStudy] = []
    for event in events:
        for ticker in event.tickers:
            study = make_study(event, ticker, bars_by_ticker.get(ticker, ()), n=n)
            if study is not None:
                rows.append(study)
    return rows
