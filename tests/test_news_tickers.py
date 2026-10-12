import logging

from app.news.events import new_event
from app.news.tickers import bind_tickers, match_tickers
from worker.news import run_rss_ingest


def test_name_dictionary_hits() -> None:
    assert match_tickers("Сбербанк вырос после отчёта") == ["SBER"]
    assert match_tickers("Газпром и Лукойл") == ["GAZP", "LKOH"]


def test_unknown_title_is_miss(caplog) -> None:
    from datetime import UTC, datetime

    row = new_event(
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        source="rss",
        source_id="x",
        title="Рынок акций вырос",
        url="https://ex/miss",
    )
    with caplog.at_level(logging.INFO, logger="news.tickers"):
        bind_tickers(row)
    assert row.tickers == []
    assert "news ticker miss" in caplog.text
    assert "Рынок акций вырос" in caplog.text


def test_ingest_binds_known_name() -> None:
    feed = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>Yandex сообщил о росте</title>
    <link>https://ex/y</link>
    <guid>y-1</guid>
    <pubDate>Mon, 12 Oct 2026 12:00:00 +0000</pubDate>
  </item>
</channel></rss>
"""
    rows = run_rss_ingest([], feed)
    assert rows[0].tickers == ["YNDX"]
