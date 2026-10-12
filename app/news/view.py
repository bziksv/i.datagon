"""Сводка ленты новостей и research для GET /news и /news/studies."""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from uuid import UUID

from app.models import NewsEvent, NewsStudy

NEWS_LIMIT = 100
STUDIES_LIMIT = 100


def news_item(row: NewsEvent) -> dict:
    return {
        "id": str(row.id),
        "ts": row.ts.isoformat() if row.ts is not None else None,
        "source": row.source,
        "source_id": row.source_id,
        "title": row.title,
        "url": row.url,
        "tickers": list(row.tickers or []),
    }


def news_view(events: Sequence[NewsEvent], *, limit: int = NEWS_LIMIT) -> dict:
    rows = sorted(
        events,
        key=lambda row: row.ts or row.source_id,
        reverse=True,
    )[:limit]
    return {"news": [news_item(row) for row in rows]}


def _money_ret(value: Decimal | float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.0001")))


def study_item(
    row: NewsStudy,
    *,
    events_by_id: Mapping[UUID, NewsEvent] | None = None,
) -> dict:
    event = (events_by_id or {}).get(row.news_event_id)
    payload = dict(row.payload or {})
    title = ""
    if event is not None:
        title = event.title
    elif payload.get("title"):
        title = str(payload["title"])
    return {
        "id": str(row.id),
        "news_event_id": str(row.news_event_id),
        "ticker": row.ticker,
        "horizon_n": int(row.horizon_n),
        "t_minus_ts": row.t_minus_ts.isoformat() if row.t_minus_ts else None,
        "t_plus_ts": row.t_plus_ts.isoformat() if row.t_plus_ts else None,
        "ret": _money_ret(row.ret),
        "title": title,
        "news_url": event.url if event is not None else None,
    }


def studies_view(
    studies: Sequence[NewsStudy],
    events: Sequence[NewsEvent] = (),
    *,
    limit: int = STUDIES_LIMIT,
) -> dict:
    by_id = {row.id: row for row in events}
    rows = sorted(
        studies,
        key=lambda row: row.t_plus_ts or row.t_minus_ts,
        reverse=True,
    )[:limit]
    return {
        "studies": [study_item(row, events_by_id=by_id) for row in rows],
    }
