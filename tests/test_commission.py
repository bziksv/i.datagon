from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.book.commission import (
    COMMISSION_REASON,
    commission_entry,
    commission_of,
    compute_equity,
    positions_value,
)
from app.book.ledger import apply_deposit, ledger_balance
from app.book.positions import apply_fill
from app.models import Fill


def _fill(*, commission: Decimal) -> Fill:
    return Fill(
        order_id=uuid4(),
        qty=10,
        price=Decimal("100"),
        commission=commission,
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        raw={},
    )


def test_zero_commission_is_posted() -> None:
    fill = _fill(commission=Decimal("0"))
    assert commission_of(fill) == Decimal("0")
    entry = commission_entry(fill, ref="c-fee-0")
    assert entry.reason == COMMISSION_REASON
    assert Decimal(str(entry.amount)) == Decimal("0")


def test_commission_is_not_lost_in_equity() -> None:
    fill = _fill(commission=Decimal("5"))
    position, buy = apply_fill(
        None,
        fill,
        sleeve="manual",
        instrument_id=uuid4(),
        side="buy",
        ref="c-fee-5",
    )
    fee = commission_entry(fill, ref="c-fee-5")
    deposit, _ = apply_deposit([])
    assert deposit is not None
    cash = ledger_balance([deposit, buy, fee])
    assert cash == Decimal("998995")
    marked = positions_value(position)
    assert marked == Decimal("1000")
    equity = compute_equity(cash, Decimal("0"), marked)
    assert equity == Decimal("999995")
    forgotten = compute_equity(ledger_balance([deposit, buy]), Decimal("0"), marked)
    assert forgotten == Decimal("1000000")
    assert equity != forgotten
