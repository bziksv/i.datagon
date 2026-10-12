from types import SimpleNamespace

import pytest

from worker.fundamentals import (
    FundamentalsRefreshError,
    asset_map_for_tickers,
    refresh_snapshots,
    target_tickers,
)
from app.models import Fundamental
from datetime import UTC, datetime


def test_asset_map_uses_asset_uid_not_instrument_uid() -> None:
    shares = [
        SimpleNamespace(ticker="SBER", uid="inst-1", asset_uid="asset-sber"),
        SimpleNamespace(ticker="GAZP", uid="inst-2", asset_uid="asset-gazp"),
        SimpleNamespace(ticker="AAPL", uid="inst-3", asset_uid="asset-aapl"),
    ]
    got = asset_map_for_tickers(shares, {"SBER", "GAZP"})
    assert got == {"asset-sber": "SBER", "asset-gazp": "GAZP"}


def test_refresh_snapshots_empty_map_raises() -> None:
    with pytest.raises(FundamentalsRefreshError, match="Нет бумаг"):
        refresh_snapshots([], {}, lambda assets: [])


def test_refresh_snapshots_fetches_by_asset_uid() -> None:
    called: list[list[str]] = []

    def fetch(assets: list[str]) -> list:
        called.append(list(assets))
        return [
            SimpleNamespace(
                asset_uid="asset-sber",
                pe_ratio_ttm=5.5,
                price_to_book_ttm=0.8,
                eps_ttm=40.0,
                market_capitalization=1.0,
                roe=0.2,
                free_float=0.4,
                dividend_yield_daily_ttm=0.08,
                currency="rub",
            )
        ]

    rows = refresh_snapshots(
        [],
        {"asset-sber": "SBER"},
        fetch,
        ts=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert called == [["asset-sber"]]
    assert len(rows) == 1
    assert rows[0].ticker == "SBER"
    assert rows[0].pe_ratio_ttm == 5.5


def test_target_tickers_includes_desk_and_existing() -> None:
    existing = [
        Fundamental(
            ticker="XYZ",
            asset_uid="a",
            ts=datetime.now(UTC),
        )
    ]
    want = target_tickers(existing)
    assert "SBER" in want
    assert "XYZ" in want
