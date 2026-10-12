from datetime import UTC, datetime

import pytest
from sqlalchemy import UniqueConstraint

from app.models import NewsEvent
from app.news.events import DuplicateNewsError, new_event, remember


def _event(*, url: str = "https://ex/a", source_id: str = "a-1") -> NewsEvent:
    return new_event(
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        source="rss",
        source_id=source_id,
        title="Note",
        url=url,
        tickers=["SBER"],
        raw={"guid": source_id},
    )


def test_news_events_columns() -> None:
    cols = set(NewsEvent.__table__.c.keys())
    assert cols >= {"ts", "source", "title", "url", "tickers", "raw"}
    names = {
        item.name
        for item in NewsEvent.__table_args__
        if isinstance(item, UniqueConstraint)
    }
    assert names == {"uq_news_events_url", "uq_news_events_source_id"}


def test_duplicate_url_rejected() -> None:
    store: list[NewsEvent] = []
    remember(store, _event(url="https://ex/a", source_id="1"))
    with pytest.raises(DuplicateNewsError, match="url"):
        remember(store, _event(url="https://ex/a", source_id="2"))


def test_duplicate_source_id_rejected() -> None:
    store: list[NewsEvent] = []
    remember(store, _event(url="https://ex/a", source_id="1"))
    with pytest.raises(DuplicateNewsError, match="source"):
        remember(store, _event(url="https://ex/b", source_id="1"))
