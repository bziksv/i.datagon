"""Разбор одного RSS 2.0 в строки news_events."""

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from app.models import NewsEvent
from app.news.events import new_event
from app.news.tickers import bind_tickers


def _text(node: ElementTree.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _ts(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return datetime.now(UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_rss(xml: str, *, source: str = "rss") -> list[NewsEvent]:
    root = ElementTree.fromstring(xml)
    rows: list[NewsEvent] = []
    for item in root.iter("item"):
        title = _text(item.find("title"))
        url = _text(item.find("link"))
        source_id = _text(item.find("guid")) or url
        if not url or not source_id:
            continue
        rows.append(
            bind_tickers(
                new_event(
                    ts=_ts(_text(item.find("pubDate"))),
                    source=source,
                    source_id=source_id,
                    title=title or url,
                    url=url,
                    tickers=[],
                    raw={"title": title, "guid": source_id, "link": url},
                )
            )
        )
    return rows
