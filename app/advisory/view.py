"""Сводки fundamentals и recommendations для API."""

from __future__ import annotations

from collections.abc import Sequence

from app.advisory.score import score_fundamental
from app.models import Fundamental

DISCLAIMER = (
    "Аналитика paper-лаборатории i.datagon. "
    "Не является индивидуальной инвестиционной рекомендацией "
    "и не услугой инвестиционного советника."
)


def fundamental_item(row: Fundamental) -> dict:
    raw = row.raw or {}
    scored = score_fundamental(
        pe_ratio_ttm=float(row.pe_ratio_ttm) if row.pe_ratio_ttm is not None else None,
        price_to_book_ttm=(
            float(row.price_to_book_ttm) if row.price_to_book_ttm is not None else None
        ),
        eps_ttm=float(row.eps_ttm) if row.eps_ttm is not None else None,
        raw=raw,
    )
    return {
        "ticker": row.ticker,
        "asset_uid": row.asset_uid,
        "ts": row.ts.isoformat() if row.ts else None,
        "pe_ratio_ttm": float(row.pe_ratio_ttm) if row.pe_ratio_ttm is not None else None,
        "price_to_book_ttm": (
            float(row.price_to_book_ttm) if row.price_to_book_ttm is not None else None
        ),
        "eps_ttm": float(row.eps_ttm) if row.eps_ttm is not None else None,
        "market_capitalization": (
            float(row.market_capitalization)
            if row.market_capitalization is not None
            else None
        ),
        "roe": raw.get("roe"),
        "free_float": raw.get("free_float"),
        "dividend_yield_ttm": raw.get("dividend_yield_daily_ttm"),
        "scores": {
            "value": scored.value,
            "quality": scored.quality,
            "div": scored.div,
            "total": scored.total,
        },
        "rationale": scored.rationale,
    }


def fundamentals_view(rows: Sequence[Fundamental]) -> dict:
    items = [fundamental_item(row) for row in rows]
    items.sort(key=lambda row: row["scores"]["total"], reverse=True)
    return {
        "items": items,
        "count": len(items),
        "disclaimer": DISCLAIMER,
    }


def recommendations_view(
    rows: Sequence[Fundamental],
    *,
    limit: int = 10,
    min_score: float = 40.0,
) -> dict:
    ranked = fundamentals_view(rows)["items"]
    picks = [
        {
            "ticker": row["ticker"],
            "side": "buy",
            "scores": row["scores"],
            "rationale": row["rationale"],
            "pe_ratio_ttm": row["pe_ratio_ttm"],
            "price_to_book_ttm": row["price_to_book_ttm"],
            "roe": row["roe"],
            "dividend_yield_ttm": row["dividend_yield_ttm"],
        }
        for row in ranked
        if row["scores"]["total"] >= min_score
    ][: max(1, int(limit))]
    return {
        "candidates": picks,
        "count": len(picks),
        "min_score": float(min_score),
        "disclaimer": DISCLAIMER,
    }
