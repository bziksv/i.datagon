"""Admission checks for reproducible backtests and paper-forward evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _iso(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def backtest_admission(report: dict[str, Any]) -> dict[str, Any]:
    backtest = report.get("backtest") or {}
    config = backtest.get("config") or {}
    summary = backtest.get("summary") or {}
    walk_forward = report.get("walk_forward") or {}
    folds = walk_forward.get("folds") or []

    no_oos_leakage = bool(folds)
    for fold in folds:
        test_start = _iso(fold.get("test_start"))
        result = fold.get("result") or {}
        warmup = int((result.get("config") or {}).get("warmup_bars") or 0)
        if test_start is None or warmup <= 0:
            no_oos_leakage = False
            break
        for fill in result.get("fills") or []:
            fill_at = _iso(fill.get("ts"))
            if fill_at is None or fill_at < test_start:
                no_oos_leakage = False
                break

    checks = [
        {
            "code": "next_bar_execution",
            "passed": config.get("execution") == "next_bar_open",
        },
        {
            "code": "cost_model_explicit",
            "passed": all(
                key in config for key in ("commission_bps", "slippage_bps")
            )
            and "costs" in summary,
        },
        {
            "code": "benchmark_same_sample",
            "passed": all(
                key in summary
                for key in ("benchmark_return", "excess_return", "total_return")
            ),
        },
        {
            "code": "walk_forward_oos",
            "passed": bool(folds) and bool(walk_forward.get("oos_summary")),
        },
        {
            "code": "no_oos_fill_before_test_start",
            "passed": no_oos_leakage,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "gate": "G2",
        "passed": passed,
        "status": "passed" if passed else "blocked",
        "checks": checks,
    }
