"""Прозрачный скор по снимку fundamentals (без LLM)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FundScore:
    value: float
    quality: float
    div: float
    total: float
    rationale: str


def _f(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clip(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 100:
        return 100.0
    return round(value, 1)


def value_score(pe: float | None, pb: float | None) -> float:
    parts: list[float] = []
    if pe is not None and pe > 0:
        if pe <= 8:
            parts.append(95.0)
        elif pe <= 12:
            parts.append(80.0)
        elif pe <= 18:
            parts.append(60.0)
        elif pe <= 25:
            parts.append(40.0)
        else:
            parts.append(15.0)
    if pb is not None and pb > 0:
        if pb <= 0.8:
            parts.append(90.0)
        elif pb <= 1.2:
            parts.append(75.0)
        elif pb <= 2.0:
            parts.append(55.0)
        elif pb <= 3.5:
            parts.append(35.0)
        else:
            parts.append(15.0)
    if not parts:
        return 0.0
    return _clip(sum(parts) / len(parts))


def quality_score(roe: float | None, eps: float | None) -> float:
    parts: list[float] = []
    if roe is not None:
        # ROE как доля (0.22) или уже в %
        roe_pct = roe * 100 if abs(roe) <= 1.5 else roe
        if roe_pct >= 20:
            parts.append(95.0)
        elif roe_pct >= 12:
            parts.append(75.0)
        elif roe_pct >= 5:
            parts.append(50.0)
        elif roe_pct > 0:
            parts.append(30.0)
        else:
            parts.append(5.0)
    if eps is not None:
        parts.append(70.0 if eps > 0 else 10.0)
    if not parts:
        return 0.0
    return _clip(sum(parts) / len(parts))


def div_score(div_yield: float | None) -> float:
    if div_yield is None:
        return 0.0
    y = div_yield * 100 if abs(div_yield) <= 1.5 else div_yield
    if y >= 10:
        return 95.0
    if y >= 7:
        return 80.0
    if y >= 4:
        return 60.0
    if y >= 2:
        return 40.0
    if y > 0:
        return 20.0
    return 0.0


def score_fundamental(
    *,
    pe_ratio_ttm: float | None = None,
    price_to_book_ttm: float | None = None,
    eps_ttm: float | None = None,
    roe: float | None = None,
    dividend_yield: float | None = None,
    raw: dict | None = None,
) -> FundScore:
    payload = raw or {}
    pe = _f(pe_ratio_ttm)
    pb = _f(price_to_book_ttm)
    eps = _f(eps_ttm)
    roe_v = _f(roe if roe is not None else payload.get("roe"))
    div = _f(
        dividend_yield
        if dividend_yield is not None
        else payload.get("dividend_yield_daily_ttm")
    )
    v = value_score(pe, pb)
    q = quality_score(roe_v, eps)
    d = div_score(div)
    # value 40% / quality 35% / div 25%; нулевые оси не тянут вниз весь вес
    weights: list[tuple[float, float]] = []
    if v > 0:
        weights.append((v, 0.40))
    if q > 0:
        weights.append((q, 0.35))
    if d > 0:
        weights.append((d, 0.25))
    if not weights:
        total = 0.0
    else:
        wsum = sum(w for _, w in weights)
        total = _clip(sum(score * (w / wsum) for score, w in weights))
    bits: list[str] = []
    if pe is not None and pe > 0:
        bits.append(f"P/E {pe:.1f}")
    if pb is not None and pb > 0:
        bits.append(f"P/B {pb:.2f}")
    if roe_v is not None:
        roe_pct = roe_v * 100 if abs(roe_v) <= 1.5 else roe_v
        bits.append(f"ROE {roe_pct:.0f}%")
    if div is not None and div > 0:
        y = div * 100 if abs(div) <= 1.5 else div
        bits.append(f"див. {y:.1f}%")
    if not bits:
        rationale = "Недостаточно фундаментальных метрик для оценки."
    else:
        rationale = (
            f"Скор {total:.0f}/100 (value {v:.0f}, quality {q:.0f}, div {d:.0f}). "
            + ", ".join(bits)
            + "."
        )
    return FundScore(value=v, quality=q, div=d, total=total, rationale=rationale)
