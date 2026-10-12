import inspect
from types import SimpleNamespace

import pytest
from app.broker.instruments import dump_moex_instruments
from app.broker.tinkoff import fetch_moex_shares
from worker.universe import run_moex_dump


def _share(ticker: str, class_code: str) -> SimpleNamespace:
    return SimpleNamespace(
        ticker=ticker,
        figi=f"FIGI-{ticker}",
        uid=f"uid-{ticker}",
        lot=10,
        currency="rub",
        class_code=class_code,
    )


def test_dump_keeps_moex_and_is_not_empty() -> None:
    shares = [
        _share("SBER", "TQBR"),
        _share("AAPL", "SPBXM"),
        _share("GAZP", "TQBR"),
    ]
    rows = run_moex_dump([], shares)
    assert rows
    tickers = {row.ticker for row in rows}
    assert tickers == {"SBER", "GAZP"}
    assert all(row.class_code == "TQBR" for row in rows)


def test_empty_moex_dump_fails() -> None:
    with pytest.raises(RuntimeError, match="empty"):
        dump_moex_instruments([], [_share("AAPL", "SPBXM")])


def test_sdk_uses_shares() -> None:
    source = inspect.getsource(fetch_moex_shares)
    assert "instruments.shares" in source
    assert "moex_share_rows" in source


@pytest.mark.skip(reason="skip-live: MOEX dump is not sent from tests")
def test_live_moex_dump() -> None:
    raise AssertionError("must stay skipped")
