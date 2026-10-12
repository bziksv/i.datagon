from copy import deepcopy
from pathlib import Path

from app.strategy.desk import desk_backtest
from app.strategy.qualification import backtest_admission


def test_real_desk_backtest_passes_g2(tmp_path, monkeypatch) -> None:
    (tmp_path / "SBER.csv").write_text(
        Path("tests/fixtures/sber_daily.csv").read_text()
    )
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    report = desk_backtest(sleeve="sma_cross", ticker="SBER")
    assert report["admission"]["gate"] == "G2"
    assert report["admission"]["passed"] is True
    assert all(check["passed"] for check in report["admission"]["checks"])


def test_fill_before_oos_boundary_blocks_g2(tmp_path, monkeypatch) -> None:
    (tmp_path / "SBER.csv").write_text(
        Path("tests/fixtures/sber_daily.csv").read_text()
    )
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    report = desk_backtest(sleeve="sma_cross", ticker="SBER")
    tampered = deepcopy(report)
    fold = tampered["walk_forward"]["folds"][0]
    if not fold["result"]["fills"]:
        fold["result"]["fills"] = [
            {"ts": "2000-01-01T00:00:00+00:00", "price": 1}
        ]
    else:
        fold["result"]["fills"][0]["ts"] = "2000-01-01T00:00:00+00:00"
    result = backtest_admission(tampered)
    assert result["passed"] is False
    check = {
        row["code"]: row["passed"] for row in result["checks"]
    }
    assert check["no_oos_fill_before_test_start"] is False
