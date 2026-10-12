import inspect
from types import SimpleNamespace

from app.broker.tinkoff import fetch_trading_status
from app.broker.trading_status import is_tradable, trading_status_view
from worker.market import is_tradable as worker_is_tradable
from worker.market import trading_status_view as worker_view


def test_normal_trading_is_tradable() -> None:
    raw = SimpleNamespace(name="SECURITY_TRADING_STATUS_NORMAL_TRADING")
    assert is_tradable(raw) is True
    assert trading_status_view(raw) == {
        "status": "SECURITY_TRADING_STATUS_NORMAL_TRADING",
        "tradable": True,
    }


def test_closed_is_not_tradable() -> None:
    raw = SimpleNamespace(name="SECURITY_TRADING_STATUS_NOT_AVAILABLE_FOR_TRADING")
    assert is_tradable(raw) is False
    assert trading_status_view(raw)["tradable"] is False


def test_worker_sees_the_field() -> None:
    raw = SimpleNamespace(name="SECURITY_TRADING_STATUS_NORMAL_TRADING")
    assert worker_is_tradable is is_tradable
    assert worker_view(raw)["tradable"] is True


def test_sdk_uses_get_trading_status() -> None:
    source = inspect.getsource(fetch_trading_status)
    assert "get_trading_status" in source
