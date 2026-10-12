from datetime import UTC, datetime, timedelta

from app.news.events import new_event
from app.news.features import news_for_bar


def _event(hour: int, source_id: str) -> object:
    return new_event(
        ts=datetime(2026, 10, 12, hour, 0, tzinfo=UTC),
        source="rss",
        source_id=source_id,
        title="Сбербанк",
        url=f"https://ex/{source_id}",
        tickers=["SBER"],
    )


def test_news_at_or_after_bar_is_not_a_feature() -> None:
    bar_ts = datetime(2026, 10, 12, 18, 0, tzinfo=UTC)
    before = _event(10, "before")
    same = _event(18, "same")
    after = new_event(
        ts=bar_ts + timedelta(minutes=1),
        source="rss",
        source_id="after",
        title="Сбербанк",
        url="https://ex/after",
        tickers=["SBER"],
    )
    seen = news_for_bar([before, same, after], bar_ts)
    assert [row.source_id for row in seen] == ["before"]
    assert same not in seen
    assert after not in seen
