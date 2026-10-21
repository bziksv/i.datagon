"""Нормализация счетов и портфеля sandbox в обычный dict."""

from decimal import Decimal
from typing import Any

from tinkoff.invest.utils import money_to_decimal, quotation_to_decimal


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return money_to_decimal(value)


def _qty(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return quotation_to_decimal(value)


def normalize_account(account: Any) -> dict[str, str]:
    status = getattr(account, "status", "")
    return {
        "broker_account_id": account.id,
        "name": getattr(account, "name", "") or "",
        "status": getattr(status, "name", None) or str(status),
    }


def normalize_portfolio(portfolio: Any) -> dict[str, Any]:
    cash_mv = getattr(portfolio, "total_amount_currencies", None)
    positions = []
    for pos in getattr(portfolio, "positions", ()) or ():
        ticker = getattr(pos, "ticker", "") or ""
        figi = getattr(pos, "figi", "") or ""
        positions.append(
            {
                "ticker": ticker or figi,
                "figi": figi,
                "instrument_type": str(getattr(pos, "instrument_type", "") or ""),
                "qty": _qty(getattr(pos, "quantity", None)),
                "avg_price": _money(getattr(pos, "average_position_price", None)),
                "current_price": _money(getattr(pos, "current_price", None)),
                "expected_yield": _qty(getattr(pos, "expected_yield", None)),
            }
        )
    return {
        "account_id": getattr(portfolio, "account_id", "") or "",
        "cash": _money(cash_mv),
        "currency": (getattr(cash_mv, "currency", None) or "rub").lower(),
        "positions": positions,
    }


def snapshot(accounts: list[Any], portfolio: Any) -> dict[str, Any]:
    return {
        "accounts": [normalize_account(item) for item in accounts],
        "portfolio": normalize_portfolio(portfolio),
    }
