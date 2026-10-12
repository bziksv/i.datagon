"""Прогон рукава по локальным свечам без брокера (desk backtest)."""

from __future__ import annotations

import os
from collections.abc import Sequence
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


def _batch_row(report: dict) -> dict:
    summary = (report.get("backtest") or {}).get("summary") or {}
    oos = (report.get("walk_forward") or {}).get("oos_summary") or {}
    evidence = report.get("evidence") or {}
    return {
        "status": "ok",
        "sleeve": report.get("sleeve"),
        "ticker": report.get("ticker"),
        "tf": report.get("tf"),
        "bars": report.get("bars"),
        "from": report.get("from"),
        "to": report.get("to"),
        "trades": summary.get("trades"),
        "net_pnl": summary.get("net_pnl"),
        "total_return": summary.get("total_return"),
        "max_drawdown": summary.get("max_drawdown"),
        "excess_return": summary.get("excess_return"),
        "oos_trades": oos.get("trades"),
        "oos_excess_return": oos.get("excess_return"),
        "capital_eligible": evidence.get("capital_eligible"),
        "evidence_score": evidence.get("score"),
        "error": None,
    }


def desk_backtest_batch(
    *,
    sleeves: Sequence[str] | None = None,
    tickers: Sequence[str] | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Прогон всех выбранных рукавов по всем доступным тикерам."""
    selected_sleeves = [
        name.strip()
        for name in (sleeves if sleeves is not None else ACTIVE_SLEEVES)
        if name and name.strip()
    ]
    unknown = [name for name in selected_sleeves if name not in ACTIVE_SLEEVES]
    if unknown:
        raise ValueError(f"unknown sleeve: {unknown[0]}")
    selected_tickers = [
        ticker.strip().upper()
        for ticker in (
            tickers if tickers is not None else list_candle_tickers(tf="1d")
        )
        if ticker and ticker.strip()
    ]
    if not selected_sleeves:
        raise ValueError("sleeves")
    if not selected_tickers:
        raise ValueError("tickers")

    rows: list[dict] = []
    for sleeve in selected_sleeves:
        for ticker in selected_tickers:
            try:
                report = desk_backtest(sleeve=sleeve, ticker=ticker, env=env)
                rows.append(_batch_row(report))
            except FileNotFoundError:
                rows.append(
                    {
                        "status": "skipped",
                        "sleeve": sleeve,
                        "ticker": ticker,
                        "tf": None,
                        "bars": None,
                        "from": None,
                        "to": None,
                        "trades": None,
                        "net_pnl": None,
                        "total_return": None,
                        "max_drawdown": None,
                        "excess_return": None,
                        "oos_trades": None,
                        "oos_excess_return": None,
                        "capital_eligible": False,
                        "evidence_score": None,
                        "error": "нет файла свечей",
                    }
                )
            except Exception as exc:  # noqa: BLE001 — сводка пакета fail-soft
                rows.append(
                    {
                        "status": "error",
                        "sleeve": sleeve,
                        "ticker": ticker,
                        "tf": None,
                        "bars": None,
                        "from": None,
                        "to": None,
                        "trades": None,
                        "net_pnl": None,
                        "total_return": None,
                        "max_drawdown": None,
                        "excess_return": None,
                        "oos_trades": None,
                        "oos_excess_return": None,
                        "capital_eligible": False,
                        "evidence_score": None,
                        "error": str(exc) or "ошибка прогона",
                    }
                )

    ok_rows = [row for row in rows if row["status"] == "ok"]
    ranked = sorted(
        ok_rows,
        key=lambda row: (
            0 if row.get("capital_eligible") else 1,
            -(row.get("oos_excess_return") or -999),
            -(row.get("total_return") or -999),
        ),
    )
    return {
        "sleeves": selected_sleeves,
        "tickers": selected_tickers,
        "count": len(rows),
        "ok": len(ok_rows),
        "skipped": sum(1 for row in rows if row["status"] == "skipped"),
        "errors": sum(1 for row in rows if row["status"] == "error"),
        "rows": rows,
        "top": ranked[:10],
    }
