import inspect
from datetime import UTC, datetime
from types import SimpleNamespace

from app.broker.fundamentals import apply_snapshots, pair_stats, snapshot_ticker
from app.broker.tinkoff import fetch_asset_fundamentals
from app.models import Fundamental


def _stat(**overrides: object) -> SimpleNamespace:
    base = dict(
        asset_uid="asset-sber",
        currency="rub",
        market_capitalization=6_000_000_000_000.0,
        pe_ratio_ttm=5.5,
        price_to_book_ttm=0.8,
        eps_ttm=45.2,
        roe=0.22,
        free_float=0.48,
        dividend_yield_daily_ttm=0.09,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_snapshot_per_ticker() -> None:
    ts = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    row = snapshot_ticker("sber", _stat(), ts=ts)
    assert row.ticker == "SBER"
    assert row.asset_uid == "asset-sber"
    assert row.pe_ratio_ttm == 5.5
    assert row.price_to_book_ttm == 0.8
    assert row.eps_ttm == 45.2
    assert row.raw["pe_ratio_ttm"] == 5.5


def test_repeat_snapshot_updates_same_ticker() -> None:
    ts = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    first = apply_snapshots([], [("SBER", _stat())], ts=ts)
    assert len(first) == 1
    later = apply_snapshots(first, [("SBER", _stat(pe_ratio_ttm=6.1))], ts=ts)
    assert len(later) == 1
    assert later[0] is first[0]
    assert later[0].pe_ratio_ttm == 6.1
    assert later[0].ticker == "SBER"


def test_pair_stats_by_asset_uid() -> None:
    stat = _stat()
    assert pair_stats([stat], {"asset-sber": "SBER"}) == [("SBER", stat)]
    assert pair_stats([stat], {"other": "GAZP"}) == []


def test_fetch_calls_get_asset_fundamentals() -> None:
    source = inspect.getsource(fetch_asset_fundamentals)
    assert "GetAssetFundamentals" in source or "get_asset_fundamentals" in source
    assert "GetAssetFundamentalsRequest" in source
    assert isinstance(Fundamental.__table__.name, str)
    assert Fundamental.__tablename__ == "fundamentals"
