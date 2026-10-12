import inspect
from decimal import Decimal
from types import SimpleNamespace

from app.broker.prices import last_price_map
from app.broker.tinkoff import last_prices_by_ticker


def test_normalize_ticker_to_price() -> None:
    raw = [
        SimpleNamespace(
            figi="BBG004",
            instrument_uid="uid-sber",
            price=SimpleNamespace(units=250, nano=500_000_000),
        ),
        SimpleNamespace(
            figi="BBG999",
            instrument_uid="uid-unknown",
            price=SimpleNamespace(units=1, nano=0),
        ),
    ]
    got = last_price_map(
        raw,
        ticker_by_figi={"BBG004": "SBER"},
        ticker_by_uid={"uid-gazp": "GAZP"},
    )
    assert got == {"SBER": Decimal("250.5")}


def test_uid_fallback() -> None:
    raw = [
        SimpleNamespace(
            figi="",
            instrument_uid="uid-1",
            price=SimpleNamespace(units=10, nano=0),
        )
    ]
    assert last_price_map(raw, ticker_by_uid={"uid-1": "SBER"}) == {
        "SBER": Decimal("10")
    }


def test_fetch_is_batch() -> None:
    source = inspect.getsource(last_prices_by_ticker)
    assert "get_last_prices" in source
    assert "figi=figis" in source
