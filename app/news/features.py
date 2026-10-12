"""Фичи бара: новость с ts ≥ бара не входит — нет lookahead."""

from collections.abc import Sequence
from datetime import datetime

from app.models import NewsEvent


def news_for_bar(
    events: Sequence[NewsEvent],
    bar_ts: datetime,
) -> list[NewsEvent]:
    return [row for row in events if row.ts < bar_ts]
