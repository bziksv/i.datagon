"""Размер позиции — доля капитала рукава на одно имя."""

from decimal import Decimal

DEFAULT_NAME_SHARE = Decimal("0.10")


def name_budget(
    capital: Decimal,
    name_share: Decimal = DEFAULT_NAME_SHARE,
) -> Decimal:
    return Decimal(capital) * Decimal(name_share)


def position_qty(
    *,
    capital: Decimal,
    price: Decimal,
    lot: int = 1,
    name_share: Decimal = DEFAULT_NAME_SHARE,
) -> int:
    budget = name_budget(capital, name_share)
    lot_cost = Decimal(price) * Decimal(lot)
    if lot_cost <= 0:
        return 0
    return int(budget // lot_cost)
