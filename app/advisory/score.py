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


# Выше ~20% TTM на РФ почти всегда разовое/битые данные брокера (как SFIN 187%).
MAX_SANE_DIV_YIELD_PCT = 20.0


def as_percent(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100 if abs(value) <= 1.5 else value


def sane_dividend_yield_pct(
    *candidates: float | None,
    max_pct: float = MAX_SANE_DIV_YIELD_PCT,
) -> float | None:
    """Первая правдоподобная див. доходность в %; выбросы отбрасываем."""
    for raw in candidates:
        y = as_percent(_f(raw))
        if y is None or y <= 0:
            continue
        if y > max_pct:
            continue
        return round(y, 2)
    return None


def div_score(div_yield: float | None) -> float:
    y = sane_dividend_yield_pct(div_yield)
    if y is None:
        return 0.0
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
    div_pct = sane_dividend_yield_pct(
        dividend_yield,
        payload.get("forward_annual_dividend_yield"),
        payload.get("dividend_yield_daily_ttm"),
        payload.get("five_years_average_dividend_yield"),
    )
    v = value_score(pe, pb)
    q = quality_score(roe_v, eps)
    d = div_score(div_pct)
    # Всегда 40/35/25: нет див./выброс = 0 по оси, вес не раздаём остальным.
    total = _clip(v * 0.40 + q * 0.35 + d * 0.25)
    bits: list[str] = []
    if pe is not None and pe > 0:
        bits.append(f"P/E {pe:.1f}")
    if pb is not None and pb > 0:
        bits.append(f"P/B {pb:.2f}")
    if roe_v is not None:
        roe_pct = as_percent(roe_v) or 0.0
        bits.append(f"ROE {roe_pct:.0f}%")
    raw_ttm = as_percent(_f(payload.get("dividend_yield_daily_ttm")))
    if div_pct is not None:
        bits.append(f"див. {div_pct:.1f}%")
    elif raw_ttm is not None and raw_ttm > MAX_SANE_DIV_YIELD_PCT:
        bits.append(f"див. выброс {raw_ttm:.0f}% (в скор как 0)")
    elif d == 0:
        bits.append("див. 0")
    if not bits:
        rationale = "Недостаточно фундаментальных метрик для оценки."
    else:
        rationale = (
            f"Скор {total:.0f}/100 (value {v:.0f}, quality {q:.0f}, div {d:.0f}). "
            + ", ".join(bits)
            + "."
        )
    return FundScore(value=v, quality=q, div=d, total=total, rationale=rationale)
