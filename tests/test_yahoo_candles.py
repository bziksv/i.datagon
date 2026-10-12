from datetime import date
from decimal import Decimal
from pathlib import Path

from app.broker.yahoo_candles import fetch_yahoo_daily, write_yahoo_csv
from app.strategy.desk import list_candle_universe


def test_fetch_yahoo_daily_parses_chart_payload() -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1700000000, 1700086400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, 11.0],
                                "high": [10.5, 11.5],
                                "low": [9.5, 10.5],
                                "close": [10.2, 11.2],
                                "volume": [1000, 2000],
                            }
                        ]
                    },
                }
            ]
        }
    }
    bars = fetch_yahoo_daily(
        "AAPL",
        from_day=date(2023, 11, 1),
        till_day=date(2023, 11, 30),
        request_json=lambda _url: payload,
    )
    assert len(bars) == 2
    assert bars[0].o == Decimal("10.0")
    assert bars[1].c == Decimal("11.2")


def test_list_candle_universe_splits_moex_and_sp500(tmp_path, monkeypatch) -> None:
    moex = tmp_path / "moex"
    sp = tmp_path / "sp"
    moex.mkdir()
    sp.mkdir()
    (moex / "SBER.csv").write_text("ts,o,h,l,c,v\n")
    (moex / "GAZP.csv").write_text("ts,o,h,l,c,v\n")
    (moex / "NLMK.csv").write_text("ts,o,h,l,c,v\n")
    # empty ignored
    (moex / "EMPTY.csv").write_text("")
    (sp / "AAPL.csv").write_text("ts,o,h,l,c,v\n")
    (sp / "MSFT.csv").write_text("ts,o,h,l,c,v\n")
    monkeypatch.setenv("CANDLE_DIR", str(moex))
    monkeypatch.setenv("CANDLE_SP500_DIR", str(sp))
    universe = list_candle_universe(tf="1d")
    assert universe["groups"]["moex"] == ["GAZP", "NLMK", "SBER"]
    assert universe["groups"]["sp500"] == ["AAPL", "MSFT"]
    assert "GAZP" in universe["tickers"] and "AAPL" in universe["tickers"]
    assert universe["count"] == 5
    sectors = {row["id"]: row for row in universe["groups"]["sectors"]}
    assert "moex_core" in sectors
    assert "SBER" in sectors["moex_core"]["tickers"]
    assert sectors["moex_core"]["default_on"] is True
    assert "moex_metals" in sectors
    assert "NLMK" in sectors["moex_metals"]["tickers"]
    assert sectors["sp500"]["tickers"] == ["AAPL", "MSFT"]


def test_write_yahoo_csv_roundtrip(tmp_path) -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1700000000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [1.0],
                                "high": [2.0],
                                "low": [0.5],
                                "close": [1.5],
                                "volume": [9],
                            }
                        ]
                    },
                }
            ]
        }
    }
    bars = fetch_yahoo_daily(
        "MSFT",
        from_day=date(2023, 11, 1),
        till_day=date(2023, 11, 2),
        request_json=lambda _url: payload,
    )
    path = write_yahoo_csv(tmp_path / "MSFT.csv", bars)
    assert path.exists()
    assert "1.5" in path.read_text()
