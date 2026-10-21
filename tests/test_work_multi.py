from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.broker.port import OrderAck
from app.work import desk_state, service


@pytest.fixture()
def desks(tmp_path, monkeypatch):
    monkeypatch.setenv("WORK_DESK_PATH", str(tmp_path / "work_desk.json"))
    monkeypatch.setenv("WORK_DESKS_DIR", str(tmp_path / "work_desks"))
    monkeypatch.setattr(service, "token_ok", lambda: True)
    return tmp_path


def _ready(desk_id: str, sleeve: str, account: str) -> dict:
    state = desk_state.empty_state(desk_id, sleeve=sleeve)
    state.update(
        {
            "account_id": account,
            "strategy_connected": True,
            "params_saved": True,
            "enabled": True,
            "sleeve_share": "0.40",
            "name_cap": "0.10",
            "created_at": datetime.now(UTC).isoformat(),
            "portfolio": {"cash": "100000", "positions": []},
        }
    )
    desk_state.save_state(state)
    return state


def test_main_desk_stays_in_legacy_file(desks) -> None:
    _ready("main", "abs_momentum_4", "acc-main")
    assert (desks / "work_desk.json").is_file()
    assert desk_state.desk_ids() == ["main"]
    with pytest.raises(ValueError):
        desk_state.load_state("../etc")
    with pytest.raises(ValueError):
        desk_state.load_state("missing")


def test_each_desk_trades_only_its_sleeve(desks, monkeypatch) -> None:
    _ready("main", "abs_momentum_4", "acc-main")
    _ready("sma-1", "sma_cross", "acc-sma")
    monkeypatch.setattr(service, "_last_close", lambda ticker: Decimal("100"))
    calls = []

    def fake_post(order, *, account_id, figi="", instrument_id=""):
        calls.append((account_id, order.ticker))
        return OrderAck(broker_order_id=f"o{len(calls)}", client_order_id=order.client_order_id, status="fill")

    monkeypatch.setattr("app.broker.tinkoff.find_moex_instrument", lambda t: SimpleNamespace(figi="F"))
    monkeypatch.setattr("app.broker.tinkoff.post_sandbox_order", fake_post)
    day = datetime(2026, 10, 20, tzinfo=UTC)
    rows = [
        SimpleNamespace(sleeve="abs_momentum_4", kind="buy", ticker="SBER", ts=day),
        SimpleNamespace(sleeve="sma_cross", kind="buy", ticker="LKOH", ts=day),
        SimpleNamespace(sleeve="rsi_reversion", kind="buy", ticker="GAZP", ts=day),
    ]
    assert service.place_signals(rows) == 2
    assert sorted(calls) == [("acc-main", "SBER"), ("acc-sma", "LKOH")]
    assert desk_state.load_state("sma-1")["trades"][0]["ticker"] == "LKOH"
    assert desk_state.load_state("main")["trades"][0]["ticker"] == "SBER"


def test_archived_desk_does_not_trade(desks, monkeypatch) -> None:
    _ready("main", "abs_momentum_4", "acc-main")
    _ready("sma-1", "sma_cross", "acc-sma")
    service.archive_desk("sma-1")
    with pytest.raises(ValueError):
        service.archive_desk("main")
    calls = []
    monkeypatch.setattr(service, "_last_close", lambda ticker: Decimal("100"))
    monkeypatch.setattr("app.broker.tinkoff.find_moex_instrument", lambda t: SimpleNamespace(figi="F"))
    monkeypatch.setattr(
        "app.broker.tinkoff.post_sandbox_order",
        lambda order, **kw: calls.append(order) or OrderAck(broker_order_id="x", client_order_id="c", status="fill"),
    )
    row = SimpleNamespace(sleeve="sma_cross", kind="buy", ticker="LKOH", ts=datetime(2026, 10, 20, tzinfo=UTC))
    assert service.place_signals([row]) == 0
    assert calls == []
    assert [d["id"] for d in service.overview()["desks"]] == ["main"]


def test_create_desk_rules(desks, monkeypatch) -> None:
    _ready("main", "abs_momentum_4", "acc-main")
    paid = []
    monkeypatch.setattr("app.broker.tinkoff.open_sandbox_account_id", lambda: "acc-new")
    monkeypatch.setattr("app.broker.tinkoff.sandbox_pay_in_rub", lambda acc, amount: paid.append((acc, amount)))
    with pytest.raises(ValueError):
        service.create_desk(sleeve="ema_scalp")
    with pytest.raises(ValueError):
        service.create_desk(sleeve="abs_momentum_4")
    with pytest.raises(ValueError):
        service.create_desk(sleeve="sma_cross", deposit="10")
    out = service.create_desk(sleeve="sma_cross", deposit="500 000")
    state = desk_state.load_state(out["desk"])
    assert state["sleeve"] == "sma_cross"
    assert state["account_id"] == "acc-new"
    assert state["strategy_connected"] is True
    assert state["enabled"] is False
    assert paid == [("acc-new", Decimal("500000.00"))]
    assert desk_state.desk_ids() == ["main", out["desk"]]
    with pytest.raises(ValueError):
        service.create_desk(sleeve="sma_cross")
    monkeypatch.setattr(service, "list_accounts", lambda: [{"broker_account_id": "acc-new"}])
    with pytest.raises(ValueError):
        service.choose_account("acc-new", "main")


def test_overview_compares_without_payins(desks) -> None:
    state = _ready("main", "abs_momentum_4", "acc-main")
    t0 = datetime.now(UTC) - timedelta(days=5)
    state["equity_curve"] = [
        {"ts": t0.isoformat(), "equity": "100000"},
        {"ts": (t0 + timedelta(days=1)).isoformat(), "equity": "90000"},
        {"ts": (t0 + timedelta(days=3)).isoformat(), "equity": "150000"},
    ]
    state["payins"] = [{"ts": (t0 + timedelta(days=2)).isoformat(), "amount": "50000"}]
    state["portfolio"] = {"cash": "160000", "positions": []}
    desk_state.save_state(state)
    row = service.overview()["desks"][0]
    assert row["pnl"] == 10000.0
    assert round(row["drawdown"], 4) == -0.1
    assert row["curve"][-1]["pct"] == 0.0
    strategies = {s["id"]: s for s in service.overview()["strategies"]}
    assert strategies["abs_momentum_4"]["used"] is True
    assert strategies["sma_cross"]["used"] is False
