from app.news.rss import parse_rss
from app.settings import Settings
from worker.news import run_rss_ingest

FEED = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Demo</title>
    <item>
      <title>First</title>
      <link>https://ex/a</link>
      <guid>a-1</guid>
      <pubDate>Mon, 12 Oct 2026 12:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Second</title>
      <link>https://ex/b</link>
      <guid>b-2</guid>
      <pubDate>Mon, 12 Oct 2026 13:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


def test_rss_url_from_config(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "t")
    monkeypatch.setenv("APP_AUTH_TOKEN", "a")
    monkeypatch.setenv("NEWS_RSS_URL", "https://example.com/feed.xml")
    assert Settings().news_rss_url == "https://example.com/feed.xml"


def test_job_puts_rows() -> None:
    rows = run_rss_ingest([], FEED)
    assert len(rows) == 2
    assert [row.url for row in rows] == ["https://ex/a", "https://ex/b"]
    assert rows[0].source == "rss"
    assert rows[0].source_id == "a-1"
    assert rows[0].title == "First"
    assert rows[0].tickers == []
    assert parse_rss(FEED)[0].raw["guid"] == "a-1"


def test_job_skips_duplicates() -> None:
    first = run_rss_ingest([], FEED)
    again = run_rss_ingest(first, FEED)
    assert len(first) == 2
    assert again == []
