"""Explainable strategy evidence score.

The score ranks research maturity; it is not a forecast of future returns.
"""

from __future__ import annotations

from typing import Any

VERSION = "v1-oos-cost-dd-paper"


def _number(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _points(value: float, maximum: int) -> int:
    return round(max(0.0, min(float(maximum), value)))


def strategy_evidence(
    report: dict[str, Any],
    *,
    paper_forward: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic 0..100 score with auditable components."""
    summary = (report.get("backtest") or {}).get("summary") or {}
    oos = ((report.get("walk_forward") or {}).get("oos_summary") or {})

    oos_excess = _number(oos.get("excess_return"))
    oos_trades = max(int(_number(oos.get("trades"))), 0)
    folds = max(int(_number(oos.get("folds"))), 0)
    drawdown = max(_number(oos.get("max_drawdown"), 1.0), 0.0)
    net_pnl = abs(_number(summary.get("net_pnl")))
    costs = max(_number(summary.get("costs")), 0.0)

    forward = paper_forward or {}
    forward_days = max(int(_number(forward.get("days"))), 0)
    forward_excess = _number(forward.get("excess_return"))

    components = {
        "oos_edge": {
            "points": _points((oos_excess / 0.05) * 30, 30),
            "max": 30,
            "value": oos_excess,
            "explanation": "Positive OOS excess return; full credit at 5%.",
        },
        "sample": {
            "points": _points((oos_trades / 20) * 20, 20),
            "max": 20,
            "value": oos_trades,
            "explanation": "OOS trade count; full credit at 20 trades.",
        },
        "drawdown": {
            "points": _points((1 - drawdown / 0.25) * 15, 15),
            "max": 15,
            "value": drawdown,
            "explanation": "OOS drawdown tolerance; zero credit at 25%.",
        },
        "cost_resilience": {
            "points": _points(
                (1 - costs / (net_pnl + costs)) * 15 if net_pnl + costs else 0,
                15,
            ),
            "max": 15,
            "value": costs,
            "explanation": "Share of net result retained after modeled costs.",
        },
        "paper_forward": {
            "points": _points(
                min(forward_days / 30, 1) * 15
                if forward_days and forward_excess > 0
                else 0,
                15,
            ),
            "max": 15,
            "value": {
                "days": forward_days,
                "excess_return": forward_excess,
                "available": bool(paper_forward),
            },
            "explanation": "Positive paper-forward evidence; full credit at 30 days.",
        },
        "walk_forward_coverage": {
            "points": _points((folds / 3) * 5, 5),
            "max": 5,
            "value": folds,
            "explanation": "Independent OOS folds; full credit at three folds.",
        },
    }
    score = sum(int(item["points"]) for item in components.values())
    blockers: list[str] = []
    if oos_trades < 5:
        blockers.append("fewer_than_5_oos_trades")
    if oos_excess <= 0:
        blockers.append("non_positive_oos_excess")
    if not paper_forward:
        blockers.append("paper_forward_missing")

    rating = "credible" if score >= 70 and not blockers else (
        "developing" if score >= 40 else "insufficient"
    )
    return {
        "version": VERSION,
        "score": score,
        "rating": rating,
        "components": components,
        "blockers": blockers,
        "capital_eligible": rating == "credible",
        "disclaimer": "Research maturity score, not a return forecast.",
    }
