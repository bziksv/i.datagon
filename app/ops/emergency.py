"""Safe in-memory emergency drills for the G4 admission gate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.book.orders import STATUS_UNKNOWN, record_and_submit
from app.broker.drills import TimeoutDrillBroker
from app.broker.fake import FakeBroker
from app.broker.port import OrderRequest
from app.risk.context import RISK_PRICE_STALE, RiskContext
from app.risk.gate import place_after_gate


def emergency_drills(*, worker_alive: bool, now: datetime | None = None) -> dict:
    observed_at = now or datetime.now(UTC)
    request = OrderRequest(
        ticker="SBER",
        side="buy",
        qty=1,
        type="market",
        client_order_id="g4-timeout-drill",
    )
    timeout_order = record_and_submit(
        request,
        sleeve="drill",
        port=TimeoutDrillBroker(),
    )

    port = FakeBroker()
    first = record_and_submit(request, sleeve="drill", port=port)
    repeated = record_and_submit(
        request,
        sleeve="drill",
        port=port,
        existing=first,
    )

    stale_context = RiskContext(
        price=Decimal("100"),
        price_as_of=observed_at - timedelta(days=3),
        equity=Decimal("1000"),
        start_equity=Decimal("1000"),
        stop_price=Decimal("90"),
        observed_at=observed_at,
    )
    limit_context = RiskContext(
        price=Decimal("100"),
        price_as_of=observed_at,
        equity=Decimal("1000"),
        start_equity=Decimal("1000"),
        stop_price=Decimal("99"),
        gross_existing=Decimal("1000"),
        observed_at=observed_at,
    )
    limited = place_after_gate(
        request,
        sleeve="drill",
        port=FakeBroker(),
        tickers=("SBER",),
        context=limit_context,
    )
    checks = [
        {
            "code": "broker_timeout_unknown",
            "passed": timeout_order.status == STATUS_UNKNOWN,
        },
        {
            "code": "duplicate_client_order_id",
            "passed": repeated is first and len(port._orders) == 1,
        },
        {
            "code": "stale_market_data_denied",
            "passed": stale_context.error() == RISK_PRICE_STALE,
        },
        {
            "code": "portfolio_limit_denied",
            "passed": limited.status == "rejected"
            and (limited.raw or {}).get("reject_reason")
            == "gross_exposure",
        },
        {
            "code": "worker_restart_recovered",
            "passed": worker_alive,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "gate": "G4",
        "passed": passed,
        "status": "passed" if passed else "blocked",
        "checks": checks,
    }
