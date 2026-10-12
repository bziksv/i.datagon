"""Строки news_events: уникальность url и пары source+source_id."""

from datetime import datetime
from uuid import uuid4

from app.models import NewsEvent


class DuplicateNewsError(ValueError):
    pass


def new_event(
    *,
    ts: datetime,
    source: str,
    source_id: str,
    title: str,
    url: str,
    tickers: list[str] | None = None,
    raw: dict | None = None,
) -> NewsEvent:
    return NewsEvent(
        id=uuid4(),
        ts=ts,
        source=source,
        source_id=source_id,
        title=title,
        url=url,
        tickers=list(tickers or []),
        raw=dict(raw or {}),
    )


def remember(existing: list[NewsEvent], row: NewsEvent) -> NewsEvent:
    for seen in existing:
        if seen.url == row.url:
            raise DuplicateNewsError(f"duplicate url {row.url}")
        if seen.source == row.source and seen.source_id == row.source_id:
            raise DuplicateNewsError(
                f"duplicate source+id {row.source}:{row.source_id}"
            )
    existing.append(row)
    return row
