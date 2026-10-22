from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.broker.port import OrderAck
from app.work import desk_state, service


@pytest.fixture()
def desk_file(tmp_path, monkeypatch):
    path = tmp_path / "work_desk.json"
    monkeypatch.setenv("WORK_DESK_PATH", str(path))
    return path


def test_wizard_rejects_full_name_and_other_steps(desk_file):
    state = desk_state.empty_state()
    with pytest.raises(ValueError):
        desk_state.set_account(state, "missing", {"known"})
    state = desk_state.set_account(state, "acc-1", {"acc-1"})
    state = desk_state.connect_strategy(state)
    with pytest.raises(ValueError):
        desk_state.save_params(state, sleeve_share="0.40", name_cap="1")
    with pytest.raises(ValueError):
        desk_state.save_params(state, sleeve_share="0.20", name_cap="0.40")
    state = desk_state.save_params(state, sleeve_share="0.40", name_cap="0.10")
    desk_state.save_state(state)
    loaded = desk_state.load_state()
    assert loaded["sleeve_share"] == "0.40"
    assert loaded["name_cap"] == "0.10"
    assert loaded["params_saved"] is True
    with pytest.raises(ValueError):
        desk_state.set_enabled(desk_state.empty_state(), True)
    enabled = desk_state.set_enabled(loaded, True)
    assert enabled["enabled"] is True
    assert desk_state.steps(enabled, token_ok=True)[-1]["ok"] is True


def test_same_signal_is_not_sent_twice(desk_file, monkeypatch):
    state = desk_state.empty_state()
    state.update(
        {
            "account_id": "acc-1",
            "strategy_connected": True,
            "params_saved": True,
            "enabled": True,
            "sleeve_share": "0.40",
            "name_cap": "0.10",
            "portfolio": {"cash": "100000", "positions": []},
        }
    )
    desk_state.save_state(state)
    monkeypatch.setattr(service, "token_ok", lambda: True)
    monkeypatch.setattr(
        service,
        "read_portfolio",
        lambda account_id: {"cash": "100000", "positions": []},
    )
    monkeypatch.setattr(service, "_last_close", lambda ticker: Decimal("100"))
    calls = []

    def fake_find(ticker):
        return SimpleNamespace(figi="FIGI")

    def fake_post(order, *, account_id, figi="", instrument_id=""):
        calls.append(order)
        return OrderAck(broker_order_id="ord-1", client_order_id=order.client_order_id, status="fill")

    monkeypatch.setattr("app.broker.tinkoff.find_moex_instrument", fake_find)
    monkeypatch.setattr("app.broker.tinkoff.post_sandbox_order", fake_post)
    row = SimpleNamespace(
        sleeve="abs_momentum_4",
        kind="buy",
        ticker="SBER",
        ts=datetime(2026, 10, 16, tzinfo=UTC),
    )
    other = SimpleNamespace(
        sleeve="abs_momentum_3",
        kind="buy",
        ticker="SBER",
        ts=row.ts,
    )
    assert service.place_signals([other]) == 0
    assert calls == []
    assert service.place_signals([row]) == 1
    assert service.place_signals([row]) == 0
    assert len(calls) == 1
    assert calls[0].qty == 100
    saved = desk_state.load_state()
    assert saved["trades"][0]["ticker"] == "SBER"
    assert saved["trades"][0]["layer"] == 1


def test_order_quantity_is_sent_in_lots(desk_file, monkeypatch):
    state = desk_state.empty_state()
    state.update(
        {
            "account_id": "acc-1",
            "strategy_connected": True,
            "params_saved": True,
            "enabled": True,
            "sleeve_share": "0.90",
            "name_cap": "0.10",
            "portfolio": {"cash": "100000", "positions": []},
        }
    )
    desk_state.save_state(state)
    monkeypatch.setattr(service, "token_ok", lambda: True)
    prices = {"GAZP": Decimal("111"), "AKRN": Decimal("18698")}
    monkeypatch.setattr(service, "_last_close", prices.__getitem__)
    lots = {"GAZP": 10, "AKRN": 1}
    monkeypatch.setattr(
        "app.broker.tinkoff.find_moex_instrument",
        lambda t: SimpleNamespace(figi=f"F-{t}", lot=lots[t]),
    )
    calls = []

    def fake_post(order, *, account_id, figi="", instrument_id=""):
        calls.append(order)
        return OrderAck(broker_order_id="o", client_order_id=order.client_order_id, status="fill")

    monkeypatch.setattr("app.broker.tinkoff.post_sandbox_order", fake_post)
    monkeypatch.setattr(service, "sleep", lambda sec: None)
    day = datetime(2026, 10, 21, tzinfo=UTC)
    rows = [
        SimpleNamespace(sleeve="abs_momentum_4", kind="buy", ticker=t, ts=day)
        for t in ("GAZP", "AKRN")
    ]
    assert service.place_signals(rows) == 1
    assert [(c.ticker, c.qty) for c in calls] == [("GAZP", 9)]
    saved = desk_state.load_state()
    assert saved["trades"][0]["qty"] == 90
    statuses = {d["ticker"]: d["status"] for d in saved["decisions"]}
    assert statuses == {"GAZP": "sent", "AKRN": "no_room_name"}
