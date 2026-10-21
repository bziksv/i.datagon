from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.work import desk_state, service
from app.work.positions import equity_at_market, position_card, position_cards


def _write_csv(path, closes, start=date(2026, 6, 1)):
    lines = ["ts,o,h,l,c,v"]
    for i, close in enumerate(closes):
        day = start + timedelta(days=i)
        lines.append(f"{day.isoformat()}T07:00:00+00:00,{close},{close},{close},{close},1000")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_equity_uses_market_price_and_skips_cash_rows() -> None:
    portfolio = {
        "cash": "1000",
        "positions": [
            {"ticker": "RUB000UTSTOM", "instrument_type": "currency", "qty": "1000", "avg_price": "1"},
            {"ticker": "SBER", "qty": "10", "avg_price": "100", "current_price": "120"},
        ],
    }
    assert equity_at_market(portfolio) == Decimal("2200")


def test_card_rising_position_holds_with_trail_armed(tmp_path) -> None:
    closes = [100 + i for i in range(60)]  # ровный рост
    _write_csv(tmp_path / "SBER.csv", closes)
    trades = [
        {"ticker": "SBER", "side": "buy", "qty": 10, "price": "130", "avg_after": "130",
         "ts": "2026-07-01T16:00:00+00:00", "layer": 1},
    ]
    card = position_card(
        {"ticker": "SBER", "qty": "10", "avg_price": "130", "current_price": "160"},
        trades=trades,
        equity=Decimal("10000"),
        name_cap=Decimal("0.10"),
        names={"SBER": "Сбербанк"},
        today=date(2026, 8, 1),
        root=tmp_path,
    )
    assert card["name"] == "Сбербанк"
    assert card["pnl"] == 300.0
    assert card["weak"]["count"] == 0
    assert card["trend"]["ratio"] > 1
    assert card["roc"]["value"] > 0
    assert card["trail"]["armed"] is True  # пик 160 / 130 ≥ 1.20
    assert card["verdict"] == "hold"
    assert card["layers"] == 1
    assert card["cap_fill"] > 1  # 1600 на 1000 потолка
    assert card["spark"]["marks"][0]["side"] == "buy"


def test_card_four_weak_days_means_exit(tmp_path) -> None:
    closes = [100 + i for i in range(45)] + [120 - 3 * i for i in range(1, 10)]
    _write_csv(tmp_path / "GAZP.csv", closes)
    card = position_card(
        {"ticker": "GAZP", "qty": "5", "avg_price": "110", "current_price": "95"},
        trades=[],
        equity=Decimal("10000"),
        name_cap=Decimal("0.10"),
        root=tmp_path,
    )
    assert card["weak"]["count"] >= 4
    assert card["verdict"] == "exit"


def test_cards_sorted_by_exit_risk(tmp_path) -> None:
    _write_csv(tmp_path / "AAA.csv", [100 + i for i in range(60)])
    _write_csv(tmp_path / "BBB.csv", [100 + i for i in range(45)] + [120 - 3 * i for i in range(1, 10)])
    cards = position_cards(
        {
            "cash": "1000",
            "positions": [
                {"ticker": "AAA", "qty": "1", "avg_price": "150", "current_price": "159"},
                {"ticker": "BBB", "qty": "1", "avg_price": "110", "current_price": "95"},
            ],
        },
        trades=[],
        name_cap=Decimal("0.10"),
        root=tmp_path,
    )
    assert [c["ticker"] for c in cards] == ["BBB", "AAA"]


def test_curve_slice_thins_week() -> None:
    now = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    curve = [
        {"ts": (now - timedelta(minutes=m)).isoformat(), "equity": str(1000 + m)}
        for m in range(60 * 24 * 3, -1, -1)
    ]
    week = service.curve_slice(curve, "week", now)
    day = service.curve_slice(curve, "day", now)
    assert len(week) < 400
    assert len(day) > len(week) / 2
    assert week[-1]["ts"] == now.isoformat()


def test_next_decision_skips_weekend() -> None:
    sat = datetime(2026, 10, 24, 10, 0, tzinfo=UTC)
    nxt = service.next_decision_at(sat)
    assert nxt.weekday() == 0
    assert (nxt.hour, nxt.minute) == (15, 50)


def test_params_resave_after_enable_and_decimal_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WORK_DESK_PATH", str(tmp_path / "desk.json"))
    state = desk_state.set_account(desk_state.empty_state(), "acc", {"acc"})
    state = desk_state.connect_strategy(state)
    state = desk_state.save_params(state, sleeve_share="0.40", name_cap="0.10")
    state = desk_state.set_enabled(state, True)
    state = desk_state.save_params(state, sleeve_share="0.50", name_cap="0.05")
    assert state["enabled"] is True
    state = desk_state.remember_mark(
        state, equity=str(Decimal("1000.5")), portfolio={"cash": Decimal("10"), "positions": []}
    )
    desk_state.save_state(state)
    loaded = desk_state.load_state()
    assert loaded["sleeve_share"] == "0.50"
    assert loaded["equity_curve"][0]["equity"] == "1000.5"


def test_disabled_signals_are_recorded(tmp_path, monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setenv("WORK_DESK_PATH", str(tmp_path / "desk.json"))
    desk_state.save_state(desk_state.empty_state())
    row = SimpleNamespace(
        sleeve="abs_momentum_4",
        kind="buy",
        ticker="SBER",
        ts=datetime(2026, 10, 16, tzinfo=UTC),
    )
    assert service.place_signals([row]) == 0
    assert service.place_signals([row]) == 0
    saved = desk_state.load_state()
    assert len(saved["decisions"]) == 1
    assert saved["decisions"][0]["status"] == "disabled"


def test_payin_value_bounds() -> None:
    assert desk_state.payin_value("500 000") == Decimal("500000.00")
    assert desk_state.payin_value("1000,5") == Decimal("1000.50")
    for bad in ("0", "999", "abc", "100000001", "-5000", "nan"):
        try:
            desk_state.payin_value(bad)
        except ValueError:
            continue
        raise AssertionError(bad)


def test_payins_after_not_counted_as_profit() -> None:
    start = datetime(2026, 10, 1, 10, tzinfo=UTC)
    payins = [
        {"ts": (start - timedelta(hours=1)).isoformat(), "amount": "1000000"},
        {"ts": (start + timedelta(days=2)).isoformat(), "amount": "500000"},
    ]
    assert service.payins_after(payins, start) == Decimal("500000")
    assert service.payins_after(payins, None) == Decimal("1500000")


def test_view_pnl_excludes_payin(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WORK_DESK_PATH", str(tmp_path / "desk.json"))
    t0 = datetime.now(UTC) - timedelta(days=3)
    state = desk_state.empty_state()
    state["equity_curve"] = [{"ts": t0.isoformat(), "equity": "1000000"}]
    state["payins"] = [{"ts": (t0 + timedelta(days=1)).isoformat(), "amount": "500000"}]
    state["portfolio"] = {"cash": "1510000", "positions": []}
    desk_state.save_state(state)
    monkeypatch.setattr(service, "token_ok", lambda: False)
    data = service.view()
    assert data["pnl_total"] == 10000.0
    assert round(data["pnl_total_pct"], 6) == round(10000 / 1500000, 6)
    assert data["payins_total"] == 500000.0
