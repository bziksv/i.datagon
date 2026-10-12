from decimal import Decimal
from types import SimpleNamespace

from app.broker.sandbox_snapshot import normalize_account, snapshot


def test_normalize_account() -> None:
    raw = SimpleNamespace(id="sbx-1", name="i.datagon", status="ACCOUNT_STATUS_OPEN")
    assert normalize_account(raw) == {
        "broker_account_id": "sbx-1",
        "name": "i.datagon",
        "status": "ACCOUNT_STATUS_OPEN",
    }


def test_snapshot_normalized_dict() -> None:
    accounts = [SimpleNamespace(id="sbx-1", name="lab", status="OPEN")]
    cash = SimpleNamespace(units=1_000_000, nano=0, currency="RUB")
    qty = SimpleNamespace(units=10, nano=0)
    price = SimpleNamespace(units=250, nano=500_000_000, currency="rub")
    portfolio = SimpleNamespace(
        account_id="sbx-1",
        total_amount_currencies=cash,
        positions=[
            SimpleNamespace(
                ticker="SBER",
                figi="BBG004",
                quantity=qty,
                average_position_price=price,
            )
        ],
    )
    got = snapshot(accounts, portfolio)
    assert got["accounts"][0]["broker_account_id"] == "sbx-1"
    assert got["portfolio"]["cash"] == Decimal("1000000")
    assert got["portfolio"]["currency"] == "rub"
    assert got["portfolio"]["positions"][0]["ticker"] == "SBER"
    assert got["portfolio"]["positions"][0]["qty"] == Decimal("10")
    assert isinstance(got, dict)
