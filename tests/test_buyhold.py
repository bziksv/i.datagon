from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.ops.buyhold import close_on_or_after, last_close, run_buyhold
from app.broker.port import CandleBar


def _write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    lines = ["ts,o,h,l,c,v"]
    for ts, close in rows:
        lines.append(f"{ts},{close},{close},{close},{close},100")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_close_on_or_after_and_last() -> None:
    # 21:00 UTC = полночь следующего дня в Москве.
    bars = [
        CandleBar(
            ts=datetime(2024, 1, 9, 21, 0, tzinfo=UTC),  # session 2024-01-10
            o=Decimal("10"),
            h=Decimal("10"),
            low=Decimal("10"),
            c=Decimal("10"),
            v=Decimal("1"),
        ),
        CandleBar(
            ts=datetime(2024, 1, 10, 21, 0, tzinfo=UTC),  # session 2024-01-11
            o=Decimal("12"),
            h=Decimal("12"),
            low=Decimal("12"),
            c=Decimal("12"),
            v=Decimal("1"),
        ),
    ]
    hit = close_on_or_after(bars, datetime(2024, 1, 11).date())
    assert hit is not None
    assert hit[0].c == Decimal("12")
    early = close_on_or_after(bars, datetime(2024, 1, 10).date())
    assert early is not None
    assert early[0].c == Decimal("10")
    last = last_close(bars)
    assert last is not None
    assert last[0].c == Decimal("12")


def test_run_buyhold_equal_and_skip(tmp_path, monkeypatch) -> None:
    moex = tmp_path / "moex"
    sp = tmp_path / "sp"
    moex.mkdir()
    sp.mkdir()
    _write_csv(
        moex / "SBER.csv",
        [
            ("2024-01-10T21:00:00+00:00", "100"),
            ("2024-06-10T21:00:00+00:00", "120"),
            ("2025-01-10T21:00:00+00:00", "150"),
        ],
    )
    _write_csv(
        moex / "GAZP.csv",
        [
            ("2024-01-10T21:00:00+00:00", "200"),
            ("2025-01-10T21:00:00+00:00", "180"),
        ],
    )
    monkeypatch.setenv("CANDLE_DIR", str(moex))
    monkeypatch.setenv("CANDLE_SP500_DIR", str(sp))
    monkeypatch.setenv("BACKTEST_COMMISSION_BPS", "0")

    out = run_buyhold(
        start="2024-01-11",
        capital=Decimal("10000"),
        tickers=["SBER", "GAZP", "MISSING"],
        commission_bps=Decimal("0"),
    )
    assert out["ok"] == 2
    assert out["skipped_n"] == 1
    assert out["skipped"][0]["ticker"] == "MISSING"
    assert out["capital"] == 10000.0
    tickers = {leg["ticker"]: leg for leg in out["legs"]}
    assert "SBER" in tickers and "GAZP" in tickers
    assert tickers["SBER"]["shares"] >= 1
    assert tickers["SBER"]["pnl"] > 0
    assert out["final_equity"] > 0


def test_run_buyhold_allocations(tmp_path, monkeypatch) -> None:
    moex = tmp_path / "moex"
    moex.mkdir()
    _write_csv(
        moex / "SBER.csv",
        [
            ("2024-01-10T21:00:00+00:00", "100"),
            ("2025-01-10T21:00:00+00:00", "200"),
        ],
    )
    monkeypatch.setenv("CANDLE_DIR", str(moex))
    monkeypatch.setenv("CANDLE_SP500_DIR", str(tmp_path / "sp"))
    out = run_buyhold(
        start="2024-01-01",
        allocations={"SBER": 1000},
        commission_bps=Decimal("0"),
    )
    assert out["ok"] == 1
    leg = out["legs"][0]
    assert leg["shares"] == 10
    assert leg["invested"] == 1000.0
    assert abs(leg["pnl_pct"] - 1.0) < 1e-9
