from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.broker.port import CandleBar
from app.models import NewsStudy
from app.news.events import new_event
from app.news.study import run_news_studies, window_bars


def _ts(day: int) -> datetime:
    return datetime(2026, 10, day, 18, 0, tzinfo=UTC)


def _bars() -> list[CandleBar]:
    closes = ["100", "101", "102", "110", "111", "112"]
    return [
        CandleBar(
            ts=_ts(10 + i),
            o=Decimal(c),
            h=Decimal(c),
            low=Decimal(c),
            c=Decimal(c),
            v=Decimal("1"),
        )
        for i, c in enumerate(closes)
    ]


def test_window_t_minus_to_t_plus_n() -> None:
    news_ts = _ts(12) - timedelta(hours=2)
    pair = window_bars(_bars(), news_ts, n=3)
    assert pair is not None
    left, right = pair
    assert left.ts == _ts(11)
    assert right.ts == _ts(15)


def test_job_writes_news_studies() -> None:
    event = new_event(
        ts=_ts(12) - timedelta(hours=2),
        source="rss",
        source_id="sber-1",
        title="Сбербанк",
        url="https://ex/sber",
        tickers=["SBER"],
    )
    rows = run_news_studies([event], {"SBER": _bars()}, n=3)
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, NewsStudy)
    assert row.news_event_id == event.id
    assert isinstance(row.news_event_id, UUID)
    assert row.ticker == "SBER"
    assert row.horizon_n == 3
    assert row.t_minus_ts == _ts(11)
    assert row.t_plus_ts == _ts(15)
    assert Decimal(str(row.ret)) == (Decimal("112") - Decimal("101")) / Decimal("101")


def test_missing_window_skipped() -> None:
    event = new_event(
        ts=_ts(20),
        source="rss",
        source_id="late",
        title="Сбербанк",
        url="https://ex/late",
        tickers=["SBER"],
    )
    assert run_news_studies([event], {"SBER": _bars()}) == []
