"""Ордер к брокеру только если все risk-гейты пропустили."""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date

from app.book.orders import (
    STATUS_REJECTED,
    draft_order,
    reject_order,
    submit_order,
)
from app.broker.port import BrokerPort, OrderRequest
from app.models import Flag, Order
from app.risk.context import RISK_CONTEXT_MISSING, RiskContext
from app.risk.daily import gate_daily_loss
from app.risk.earnings import gate_earnings
from app.risk.kill import gate_kill
from app.risk.name import gate_name_weight
from app.risk.once import gate_once_per_bar
from app.risk.portfolio import gate_portfolio
from app.risk.size import gate_trade_risk
from app.risk.sleeve import gate_sleeve_weight
from app.risk.universe import gate_universe

RISK_POLICY_VERSION = "risk-v1"


def place_after_gate(
    request: OrderRequest,
    *,
    sleeve: str,
    port: BrokerPort | None,
    tickers: Iterable[str],
    flags: Sequence[Flag] = (),
    calendar: Mapping[str, Iterable[date]] | None = None,
    day: date | None = None,
    entered: Iterable[str] = (),
    context: RiskContext | None = None,
    defer_submit: bool = False,
) -> Order:
    order = draft_order(request, sleeve=sleeve)
    audit: list[dict] = []
    universe_tickers = tuple(tickers)
    entered_tickers = tuple(entered)
    decision_day = day or date.min

    def record(code: str, gated: Order, inputs: dict | None = None) -> Order:
        reason = (gated.raw or {}).get("reject_reason")
        audit.append(
            {
                "code": code,
                "outcome": "deny" if gated.status == STATUS_REJECTED else "allow",
                "reason": reason,
                "explanation": reason or "check_passed",
                "inputs": inputs or {},
            }
        )
        raw = dict(gated.raw or {})
        raw["risk_policy_version"] = RISK_POLICY_VERSION
        raw["risk_checks"] = list(audit)
        gated.raw = raw
        return gated

    checks = (
        ("universe", lambda: gate_universe(order, universe_tickers)),
        ("kill_switch", lambda: gate_kill(order, flags)),
        ("once_per_bar", lambda: gate_once_per_bar(order, entered_tickers)),
        ("earnings", lambda: gate_earnings(order, calendar or {}, decision_day)),
    )
    for code, check in checks:
        inputs = {
            "universe": {
                "ticker": order.ticker,
                "allowed": order.ticker in universe_tickers,
            },
            "kill_switch": {
                "flags": {
                    flag.key: bool(flag.value)
                    for flag in flags
                }
            },
            "once_per_bar": {
                "ticker": order.ticker,
                "already_entered": order.ticker in entered_tickers,
            },
            "earnings": {
                "ticker": order.ticker,
                "day": decision_day.isoformat(),
            },
        }[code]
        gated = record(code, check(), inputs)
        if gated.status == STATUS_REJECTED:
            return gated
    if order.side == "buy":
        if context is None:
            return record(
                "risk_context",
                reject_order(order, RISK_CONTEXT_MISSING),
                {"present": False},
            )
        context_error = context.error()
        if context_error is not None:
            return record(
                "risk_context",
                reject_order(order, context_error),
                context.snapshot(),
            )
        raw = dict(order.raw or {})
        raw["risk_context"] = context.snapshot()
        order.raw = raw
        record("risk_context", order, context.snapshot())
        from app.risk.params_store import load_name_share

        risk_checks = (
            (
                "trade_risk",
                lambda: gate_trade_risk(
                    order,
                    price=context.price,
                    stop_price=context.stop_price,
                    equity=context.equity,
                ),
            ),
            (
                "portfolio",
                lambda: gate_portfolio(
                    order,
                    price=context.price,
                    equity=context.equity,
                    gross_existing=context.gross_existing,
                    max_drawdown=context.max_drawdown,
                ),
            ),
            (
                "name_concentration",
                lambda: gate_name_weight(
                    order,
                    price=context.price,
                    equity=context.equity,
                    existing=context.name_existing,
                    limit=load_name_share(),
                ),
            ),
            (
                "sleeve_exposure",
                lambda: gate_sleeve_weight(
                    order,
                    price=context.price,
                    equity=context.equity,
                    existing=context.sleeve_existing,
                ),
            ),
            (
                "daily_loss",
                lambda: gate_daily_loss(
                    order,
                    start_equity=context.start_equity,
                    equity=context.equity,
                ),
            ),
        )
        for code, check in risk_checks:
            gated = record(code, check(), context.snapshot())
            if gated.status == STATUS_REJECTED:
                return gated
    if defer_submit:
        return record(
            "persistence_barrier",
            order,
            {"required_before_broker_submit": True},
        )
    return record(
        "broker_submit",
        submit_order(order, port, request),
        {"client_order_id": request.client_order_id},
    )
