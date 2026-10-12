from decimal import Decimal
from uuid import uuid4

from app.book.vault import sweep, vault_cut
from app.models import Position
from app.strategy.view import position_pnl


def test_price_up_does_not_grow_vault() -> None:
    position = Position(
        sleeve="sma_cross",
        instrument_id=uuid4(),
        qty=10,
        avg_price=Decimal("100"),
    )
    vault = Decimal("5000")
    unrealized = position_pnl(position, Decimal("110"))
    assert unrealized == Decimal("100")
    assert sweep(vault, realized=Decimal("0")) == vault
    assert vault_cut(Decimal("0"), vault=vault) == Decimal("0")
    assert sweep(vault, realized=unrealized) == Decimal("5050")
