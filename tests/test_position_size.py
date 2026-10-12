from decimal import Decimal

from app.strategy.size import name_budget, position_qty


def test_one_million_ten_percent_name() -> None:
    capital = Decimal("1000000")
    assert name_budget(capital) == Decimal("100000")
    assert position_qty(capital=capital, price=Decimal("250"), lot=1) == 400
    assert position_qty(capital=capital, price=Decimal("250"), lot=10) == 40
