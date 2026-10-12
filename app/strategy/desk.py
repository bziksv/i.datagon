"""Прогон рукава по локальным свечам без брокера (desk backtest)."""

from __future__ import annotations

import os
from pathlib import Path

from app.alloc.view import ACTIVE_SLEEVES
from app.strategy.backtest import load_bars, replay
from app.strategy.config import (
    donchian_from_config,
    rsi_from_config,
    scalp_from_config,
    sma_from_config,
)
from app.strategy.donchian import SLEEVE as DONCHIAN_SLEEVE
from app.strategy.rsi import SLEEVE as RSI_SLEEVE
from app.strategy.scalp import SLEEVE as SCALP_SLEEVE
from app.strategy.sma import SLEEVE as SMA_SLEEVE


def candle_dir() -> Path:
    return Path(os.environ.get("CANDLE_DIR", "data/candles"))


def candle_m15_dir() -> Path:
    return Path(os.environ.get("CANDLE_M15_DIR", "data/candles_m15"))


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
    kinds: dict[str, int] = {}
    for row in signals:
        kinds[row.kind] = kinds.get(row.kind, 0) + 1
    tf = getattr(strategy, "timeframe", "1d")
    actionable = [row for row in signals if row.kind != "flat"]
    tail = actionable[-12:] if actionable else signals[-12:]
    return {
        "sleeve": name,
        "ticker": symbol,
        "tf": tf,
        "bars": len(bars),
        "signals": len(signals),
        "kinds": kinds,
        "path": str(path),
        "last": [
            {
                "ts": row.ts.isoformat() if row.ts else None,
                "kind": row.kind,
                "ticker": row.ticker,
            }
            for row in tail
        ],
    }
