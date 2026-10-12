"""Correlation-aware inverse-volatility risk budgets."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal


def _volatility(values: Sequence[float]) -> float | None:
    rows = [float(value) for value in values]
    if len(rows) < 2:
        return None
    mean = sum(rows) / len(rows)
    variance = sum((value - mean) ** 2 for value in rows) / (len(rows) - 1)
    return math.sqrt(variance)


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    size = min(len(left), len(right))
    if size < 3:
        return None
    x = [float(value) for value in left[-size:]]
    y = [float(value) for value in right[-size:]]
    x_mean = sum(x) / size
    y_mean = sum(y) / size
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    x_var = sum((a - x_mean) ** 2 for a in x)
    y_var = sum((b - y_mean) ** 2 for b in y)
    if x_var <= 0 or y_var <= 0:
        return None
    return numerator / math.sqrt(x_var * y_var)


def risk_budget_weights(
    sleeves: Sequence[str],
    returns: Mapping[str, Sequence[float]],
) -> dict[str, Decimal]:
    """Allocate more to lower-volatility, less-correlated qualified sleeves."""
    names = list(sleeves)
    if not names:
        return {}
    raw: dict[str, Decimal] = {}
    for name in names:
        volatility = _volatility(returns.get(name, ()))
        if volatility is None or volatility <= 0:
            raw[name] = Decimal("1")
            continue
        correlations = [
            max(correlation, 0.0)
            for other in names
            if other != name
            and (
                correlation := _correlation(
                    returns.get(name, ()),
                    returns.get(other, ()),
                )
            )
            is not None
        ]
        average_positive_correlation = (
            sum(correlations) / len(correlations) if correlations else 0.0
        )
        score = (1 / volatility) / (1 + average_positive_correlation)
        raw[name] = Decimal(str(score))
    total = sum(raw.values(), Decimal("0"))
    if total <= 0:
        equal = Decimal("1") / Decimal(len(names))
        return {name: equal for name in names}
    return {name: value / total for name, value in raw.items()}
