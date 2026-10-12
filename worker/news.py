"""Джоба: ingest одного RSS в news_events."""

from collections.abc import Sequence

from app.models import NewsEvent
from app.news.events import DuplicateNewsError, remember
from app.news.rss import parse_rss


def run_rss_ingest(
    existing: Sequence[NewsEvent],
    xml: str,
    *,
    source: str = "rss",
) -> list[NewsEvent]:
    store = list(existing)
    added: list[NewsEvent] = []
    for row in parse_rss(xml, source=source):
        try:
            remember(store, row)
        except DuplicateNewsError:
            continue
        added.append(row)
    return added
