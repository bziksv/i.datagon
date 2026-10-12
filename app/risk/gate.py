"""Ордер к брокеру только если все risk-гейты пропустили."""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal

from app.book.orders import STATUS_REJECTED, draft_order, submit_order
from app.broker.port import BrokerPort, OrderRequest
from app.models import Flag, Order
from app.risk.daily import gate_daily_loss
from app.risk.earnings import gate_earnings
from app.risk.kill import gate_kill
from app.risk.name import gate_name_weight
from app.risk.once import gate_once_per_bar
from app.risk.sleeve import gate_sleeve_weight
from app.risk.universe import gate_universe


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
    price: Decimal | None = None,
    equity: Decimal | None = None,
    start_equity: Decimal | None = None,
    name_existing: Decimal = Decimal("0"),
    sleeve_existing: Decimal = Decimal("0"),
) -> Order:
    order = draft_order(request, sleeve=sleeve)
    checks = [
        gate_universe(order, tickers),
        gate_kill(order, flags),
        gate_once_per_bar(order, entered),
        gate_earnings(order, calendar or {}, day or date.min),
    ]
    if price is not None and equity is not None:
        from app.risk.params_store import load_name_share

        checks.append(
            gate_name_weight(
                order,
                price=price,
                equity=equity,
                existing=name_existing,
                limit=load_name_share(),
            )
        )
        checks.append(
            gate_sleeve_weight(
                order, price=price, equity=equity, existing=sleeve_existing
            )
        )
        checks.append(
            gate_daily_loss(
                order,
                start_equity=start_equity if start_equity is not None else equity,
                equity=equity,
            )
        )
    for gated in checks:
        if gated.status == STATUS_REJECTED:
            return gated
    return submit_order(order, port, request)
