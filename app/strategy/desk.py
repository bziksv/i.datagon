"""Прогон рукава по локальным свечам без брокера (desk backtest)."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

from app.alloc.view import ACTIVE_SLEEVES
from app.strategy.backtest import (
    BacktestConfig,
    load_bars,
    replay,
    run_backtest,
    run_walk_forward,
)
from app.strategy.config import (
    donchian_from_config,
    rsi_from_config,
    scalp_from_config,
    sma_from_config,
)
from app.strategy.donchian import SLEEVE as DONCHIAN_SLEEVE
from app.strategy.evidence import strategy_evidence
from app.strategy.qualification import backtest_admission
from app.strategy.rsi import SLEEVE as RSI_SLEEVE
from app.strategy.scalp import SLEEVE as SCALP_SLEEVE
from app.strategy.sma import SLEEVE as SMA_SLEEVE


def candle_dir() -> Path:
    return Path(os.environ.get("CANDLE_DIR", "data/candles"))


def candle_m15_dir() -> Path:
    return Path(os.environ.get("CANDLE_M15_DIR", "data/candles_m15"))


def list_candle_tickers(*, tf: str = "1d") -> list[str]:
    root = candle_m15_dir() if tf == "15m" else candle_dir()
    if not root.is_dir():
        return []
    return sorted(
        path.stem.upper()
        for path in root.glob("*.csv")
        if path.is_file() and path.stat().st_size > 0
    )


def strategy_for(sleeve: str, env: dict[str, str] | None = None):
    env = env if env is not None else dict(os.environ)
    if sleeve == SMA_SLEEVE:
        return sma_from_config(env)
    if sleeve == DONCHIAN_SLEEVE:
        return donchian_from_config(env)
    if sleeve == RSI_SLEEVE:
        return rsi_from_config(env)
    if sleeve == SCALP_SLEEVE:
        return scalp_from_config(env)
    raise ValueError(f"unknown sleeve: {sleeve}")


def _bars_path(sleeve: str, symbol: str) -> Path:
    daily = candle_dir() / f"{symbol}.csv"
    if sleeve == SCALP_SLEEVE:
        m15 = candle_m15_dir() / f"{symbol}.csv"
        if m15.exists():
            return m15
    return daily


def desk_backtest(
    *,
    sleeve: str,
    ticker: str,
    env: dict[str, str] | None = None,
) -> dict:
    name = sleeve.strip()
    if name not in ACTIVE_SLEEVES:
        raise ValueError("unknown sleeve")
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("ticker")
    path = _bars_path(name, symbol)
    if not path.exists():
        raise FileNotFoundError(str(path))
    bars = load_bars(path)
    strategy = strategy_for(name, env)
    signals = replay(strategy, symbol, bars)
    config_values = env if env is not None else dict(os.environ)
    tf = getattr(strategy, "timeframe", "1d")
    backtest_config = BacktestConfig(
        initial_cash=Decimal(config_values.get("BACKTEST_INITIAL_CASH", "1000000")),
        position_share=Decimal(
            config_values.get("BACKTEST_POSITION_SHARE", "0.10")
        ),
        commission_bps=Decimal(config_values.get("BACKTEST_COMMISSION_BPS", "5")),
        slippage_bps=Decimal(config_values.get("BACKTEST_SLIPPAGE_BPS", "5")),
        lot=int(config_values.get("BACKTEST_LOT", "1")),
        periods_per_year=(
            int(config_values.get("BACKTEST_PERIODS_PER_YEAR", "6552"))
            if tf == "15m"
            else int(config_values.get("BACKTEST_PERIODS_PER_YEAR", "252"))
        ),
    )
    report = run_backtest(
        strategy,
        symbol,
        bars,
        config=backtest_config,
    )
    oos_share = Decimal(config_values.get("BACKTEST_OOS_SHARE", "0.30"))
    if not Decimal("0") < oos_share < Decimal("1"):
        raise ValueError("BACKTEST_OOS_SHARE must be in (0, 1)")
    oos_bars = max(int(Decimal(len(bars)) * oos_share), 1)
    train_bars = len(bars) - oos_bars
    walk_forward = (
        run_walk_forward(
            lambda: strategy_for(name, env),
            symbol,
            bars,
            train_bars=train_bars,
            test_bars=max(
                int(config_values.get("BACKTEST_OOS_FOLD_BARS", str(oos_bars))),
                1,
            ),
            config=backtest_config,
        )
        if train_bars >= 1
        else None
    )
    kinds: dict[str, int] = {}
    for row in signals:
        kinds[row.kind] = kinds.get(row.kind, 0) + 1
    actionable = [row for row in signals if row.kind != "flat"]
    tail = actionable[-12:] if actionable else signals[-12:]
    period_from = bars[0].ts.isoformat() if bars else None
    period_to = bars[-1].ts.isoformat() if bars else None
    evaluation_start = (report.get("config") or {}).get("evaluation_start")
    report = {
        "sleeve": name,
        "ticker": symbol,
        "tf": tf,
        "bars": len(bars),
        "from": period_from,
        "to": period_to,
        "evaluation_start": evaluation_start,
        "signals": len(signals),
        "kinds": kinds,
        "path": str(path),
        "backtest": report,
        "walk_forward": walk_forward,
        "last": [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "kind": row.kind,
                "ticker": row.ticker,
            }
            for row in tail
        ],
    }
    report["admission"] = backtest_admission(report)
    report["evidence"] = strategy_evidence(report)
    return report
