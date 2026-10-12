from decimal import Decimal

from app.book.ledger import DEFAULT_DEPOSIT
from app.book.vault import apply_closes, vault_cut


def test_twenty_percent_after_one_million_withdrawn() -> None:
    covered = apply_closes([Decimal("2000000")], deposit=DEFAULT_DEPOSIT)
    assert covered == DEFAULT_DEPOSIT
    assert vault_cut(Decimal("100000"), vault=covered) == Decimal("20000")

    after = apply_closes(
        [Decimal("2000000"), Decimal("100000")],
        deposit=DEFAULT_DEPOSIT,
    )
    assert after == Decimal("1020000")
