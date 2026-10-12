"""Accounting identities used by the G1 admission gate."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def _decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def accounting_reconciliation(
    valuation: dict[str, Any],
    *,
    tolerance: Decimal = Decimal("0.01"),
) -> dict[str, Any]:
    """Explain equity and PnL without treating incomplete valuation as zero."""
    if valuation.get("status") != "complete" or valuation.get("equity") is None:
        return {
            "passed": False,
            "status": "blocked",
            "reason": "valuation_incomplete",
            "checks": [],
        }

    cash = _decimal(valuation.get("cash"))
    vault = _decimal(valuation.get("vault"))
    market = _decimal(valuation.get("known_market_value"))
    equity = _decimal(valuation.get("equity"))
    cost_basis = _decimal(valuation.get("positions_cost_basis"))
    unrealized = _decimal(valuation.get("unrealized_pnl"))
    realized_net = _decimal(valuation.get("realized_net_pnl"))
    events = valuation.get("cash_events") or {}
    external_flows = _decimal(events.get("deposit")) + _decimal(
        events.get("withdrawal")
    )
    operating_events = (
        _decimal(events.get("dividend"))
        + _decimal(events.get("fee"))
        + _decimal(events.get("tax"))
    )

    checks = [
        {
            "code": "equity_identity",
            "actual": equity,
            "expected": cash + vault + market,
        },
        {
            "code": "unrealized_identity",
            "actual": unrealized,
            "expected": market - cost_basis,
        },
        {
            "code": "pnl_identity",
            "actual": equity - external_flows,
            "expected": realized_net + unrealized + operating_events,
        },
    ]
    for check in checks:
        delta = check["actual"] - check["expected"]
        check["delta"] = float(delta)
        check["passed"] = abs(delta) <= tolerance
        check["actual"] = float(check["actual"])
        check["expected"] = float(check["expected"])
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "reason": None if passed else "accounting_identity_mismatch",
        "tolerance": float(tolerance),
        "checks": checks,
    }
