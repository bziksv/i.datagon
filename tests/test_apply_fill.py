from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.book.accounts import TRADING_CASH
from app.book.ledger import apply_deposit, ledger_balance
from app.book.positions import apply_fill, apply_fills
from app.models import Fill


def _fill(qty: int, price: str) -> Fill:
    return Fill(
        order_id=uuid4(),
        qty=qty,
        price=Decimal(price),
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        raw={"price": price},
    )


def test_buy_fill_qty_avg_and_ledger() -> None:
    instrument_id = uuid4()
    fill = _fill(10, "100")
    position, entry = apply_fill(
        None,
        fill,
        sleeve="manual",
        instrument_id=instrument_id,
        side="buy",
        ref="c-fill-1",
    )
    assert position.qty == 10
    assert Decimal(str(position.avg_price)) == Decimal("100")
    assert position.instrument_id == instrument_id
    assert entry.account_kind == TRADING_CASH
    assert entry.reason == "fill"
    assert Decimal(str(entry.amount)) == Decimal("-1000")

    deposit, cash = apply_deposit([])
    assert deposit is not None
    assert ledger_balance([deposit, entry]) == Decimal("999000")
    assert cash + Decimal(str(entry.amount)) == Decimal("999000")


def test_sell_keeps_avg_price() -> None:
    instrument_id = uuid4()
    long, _buy = apply_fill(
        None,
        _fill(10, "100"),
        sleeve="manual",
        instrument_id=instrument_id,
        side="buy",
    )
    left, sell = apply_fill(
        long,
        _fill(4, "110"),
        sleeve="manual",
        instrument_id=instrument_id,
        side="sell",
    )
    assert left.qty == 6
    assert Decimal(str(left.avg_price)) == Decimal("100")
    assert Decimal(str(sell.amount)) == Decimal("440")


def test_two_partial_fills_recalc_qty_and_avg() -> None:
    instrument_id = uuid4()
    order_id = uuid4()
    first = _fill(4, "100")
    second = _fill(6, "110")
    first.order_id = order_id
    second.order_id = order_id
    position, entries = apply_fills(
        None,
        [first, second],
        sleeve="manual",
        instrument_id=instrument_id,
        side="buy",
        ref="c-partial-1",
    )
    assert position is not None
    assert position.qty == 10
    assert Decimal(str(position.avg_price)) == Decimal("106")
    assert len(entries) == 2
    assert Decimal(str(entries[0].amount)) == Decimal("-400")
    assert Decimal(str(entries[1].amount)) == Decimal("-660")
