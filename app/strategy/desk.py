"""Прогон рукава по локальным свечам без брокера (desk backtest)."""

from __future__ import annotations

import os
from collections import defaultdict
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
from app.strategy.abs_mom import SLEEVE as ABS_MOM_SLEEVE
from app.strategy.config import (
    abs_mom_from_config,
    donchian_from_config,
    morning_from_config,
    overnight_from_config,
    rsi_from_config,
    scalp_from_config,
    sma_from_config,
)
from app.strategy.moex_groups import (
    MOEX_DESK_CORE,
    filter_sectors_by_available,
)
from app.strategy.donchian import SLEEVE as DONCHIAN_SLEEVE
from app.strategy.evidence import strategy_evidence
from app.strategy.morning import SLEEVE as MORNING_SLEEVE
from app.strategy.overnight import SLEEVE as OVERNIGHT_SLEEVE
from app.strategy.qualification import backtest_admission
from app.strategy.rsi import SLEEVE as RSI_SLEEVE
from app.strategy.scalp import SLEEVE as SCALP_SLEEVE
from app.strategy.sma import SLEEVE as SMA_SLEEVE


def candle_dir() -> Path:
    return Path(os.environ.get("CANDLE_DIR", "data/candles"))


def candle_m15_dir() -> Path:
    return Path(os.environ.get("CANDLE_M15_DIR", "data/candles_m15"))


def candle_sp500_dir() -> Path:
    return Path(os.environ.get("CANDLE_SP500_DIR", "data/candles_sp500"))


def _list_csv_tickers(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(
        path.stem.upper()
        for path in root.glob("*.csv")
        if path.is_file() and path.stat().st_size > 0
    )


def list_candle_tickers(*, tf: str = "1d") -> list[str]:
    if tf == "15m":
        return _list_csv_tickers(candle_m15_dir())
    universe = list_candle_universe(tf=tf)
    return list(universe["tickers"])


def list_candle_universe(*, tf: str = "1d") -> dict:
    """MOEX (по отраслям) и S&P 500; плоский tickers — для batch/API."""
    if tf == "15m":
        m15 = _list_csv_tickers(candle_m15_dir())
        return {
            "tf": "15m",
            "tickers": m15,
            "count": len(m15),
            "groups": {
                "moex": m15,
                "sp500": [],
                "sectors": [
                    {
                        "id": "moex_m15",
                        "title": "MOEX · M15",
                        "default_on": True,
                        "tickers": m15,
                    }
                ],
            },
        }
    moex = _list_csv_tickers(candle_dir())
    sp500 = _list_csv_tickers(candle_sp500_dir())
    moex_set = set(moex)
    sp_only = [name for name in sp500 if name not in moex_set]
    sectors = filter_sectors_by_available(moex)
    # тикеры вне отраслевого справочника — отдельная куча
    known = {name for sector in sectors for name in sector["tickers"]}
    extra = [name for name in moex if name not in known]
    if extra:
        sectors.append(
            {
                "id": "moex_other",
                "title": "MOEX · прочее",
                "default_on": False,
                "tickers": extra,
            }
        )
    if sp_only:
        sectors.append(
            {
                "id": "sp500",
                "title": "S&P 500",
                "default_on": False,
                "tickers": sp_only,
            }
        )
    # ядро сначала в плоском списке, потом остальные MOEX, потом S&P
    core = [name for name in MOEX_DESK_CORE if name in moex_set]
    rest_moex = [name for name in moex if name not in set(core)]
    tickers = core + rest_moex + sp_only
    return {
        "tf": "1d",
        "tickers": tickers,
        "count": len(tickers),
        "groups": {
            "moex": moex,
            "sp500": sp_only,
            "sectors": sectors,
        },
    }


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
    if sleeve == OVERNIGHT_SLEEVE:
        return overnight_from_config(env)
    if sleeve == MORNING_SLEEVE:
        return morning_from_config(env)
    if sleeve == ABS_MOM_SLEEVE:
        return abs_mom_from_config(env)
    raise ValueError(f"unknown sleeve: {sleeve}")


def _bars_path(sleeve: str, symbol: str) -> Path:
    if sleeve == SCALP_SLEEVE:
        m15 = candle_m15_dir() / f"{symbol}.csv"
        if m15.exists():
            return m15
    daily = candle_dir() / f"{symbol}.csv"
    if daily.exists():
        return daily
    sp500 = candle_sp500_dir() / f"{symbol}.csv"
    if sp500.exists():
        return sp500
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
    share_attr = getattr(strategy, "backtest_position_share", None)
    position_share = (
        Decimal(str(share_attr))
        if share_attr is not None
        else Decimal(config_values.get("BACKTEST_POSITION_SHARE", "0.10"))
    )
    backtest_config = BacktestConfig(
        initial_cash=Decimal(config_values.get("BACKTEST_INITIAL_CASH", "1000000")),
        position_share=position_share,
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


def _batch_trade_rows(report: dict) -> list[dict]:
    raw = (report.get("backtest") or {}).get("trades") or []
    rows: list[dict] = []
    for trade in raw:
        qty = int(trade.get("qty") or 0)
        entry_price = trade.get("entry_price")
        try:
            notional = (
                round(float(entry_price) * qty, 2)
                if entry_price is not None
                else None
            )
        except (TypeError, ValueError):
            notional = None
        rows.append(
            {
                "entry_ts": trade.get("entry_ts"),
                "exit_ts": trade.get("exit_ts"),
                "qty": qty,
                "entry_price": entry_price,
                "exit_price": trade.get("exit_price"),
                "notional": notional,
                "net_pnl": trade.get("net_pnl"),
                "exit_reason": trade.get("exit_reason"),
            }
        )
    return rows


def _downsample_curve(
    points: Sequence[dict],
    *,
    max_points: int = 100,
) -> list[dict]:
    if not points:
        return []
    if len(points) <= max_points or max_points < 2:
        return [
            {"ts": point["ts"], "equity": float(point["equity"])}
            for point in points
        ]
    last_idx = len(points) - 1
    out: list[dict] = []
    prev_idx = -1
    for step in range(max_points):
        idx = round(step * last_idx / (max_points - 1))
        if idx == prev_idx:
            continue
        prev_idx = idx
        point = points[idx]
        out.append({"ts": point["ts"], "equity": float(point["equity"])})
    return out


def _combine_equity_curves(curves: Sequence[Sequence[dict]]) -> list[dict]:
    """Портфель с равным стартовым кэшем: сумма equity по тикерам с ffill."""
    series: list[dict[str, float]] = []
    all_ts: set[str] = set()
    for curve in curves:
        mapping: dict[str, float] = {}
        for point in curve:
            ts = str(point.get("ts") or "")
            if not ts:
                continue
            try:
                mapping[ts] = float(point["equity"])
            except (KeyError, TypeError, ValueError):
                continue
            all_ts.add(ts)
        if mapping:
            series.append(mapping)
    if not series:
        return []
    last: list[float | None] = [None] * len(series)
    out: list[dict] = []
    for ts in sorted(all_ts):
        total = 0.0
        ready = 0
        for index, mapping in enumerate(series):
            if ts in mapping:
                last[index] = mapping[ts]
            if last[index] is not None:
                total += float(last[index])
                ready += 1
        if ready == len(series):
            out.append({"ts": ts, "equity": round(total, 2)})
    return out


def _curve_max_drawdown(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return abs(worst)


def _sleeve_batch_summary(
    sleeve: str,
    parts: Sequence[dict],
) -> dict:
    """Итог рукава по всем тикерам: PnL, пик, просадка, кривая портфеля."""
    ok_parts = [part for part in parts if part.get("curve")]
    tickers = sorted({str(part["ticker"]) for part in parts})
    trades = sum(int(part.get("trades") or 0) for part in parts)
    pnls = [
        float(part["net_pnl"])
        for part in parts
        if part.get("net_pnl") is not None
    ]
    returns = [
        float(part["total_return"])
        for part in parts
        if part.get("total_return") is not None
    ]
    name_dds = [
        float(part["max_drawdown"])
        for part in parts
        if part.get("max_drawdown") is not None
    ]
    net_pnl = round(sum(pnls), 2) if pnls else None
    avg_return = (sum(returns) / len(returns)) if returns else None
    win_tickers = sum(1 for value in returns if value > 0)
    initials = [
        float(part["initial_cash"])
        for part in parts
        if part.get("initial_cash") is not None
    ]
    initial_cash = round(sum(initials), 2) if initials else None
    portfolio = _downsample_curve(
        _combine_equity_curves([part["curve"] for part in ok_parts])
    )
    equities = [float(point["equity"]) for point in portfolio]
    if equities and initial_cash and initial_cash > 0:
        peak_equity = max(equities)
        final_equity = equities[-1]
        total_return = final_equity / initial_cash - 1.0
        max_drawdown = _curve_max_drawdown(equities)
        peak_return = peak_equity / initial_cash - 1.0
    else:
        peak_equity = None
        final_equity = None
        total_return = avg_return
        max_drawdown = max(name_dds) if name_dds else None
        peak_return = max(returns) if returns else None
    return {
        "sleeve": sleeve,
        "tickers": tickers,
        "ok": len(parts),
        "trades": trades,
        "net_pnl": net_pnl,
        "avg_return": avg_return,
        "total_return": total_return,
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "peak_equity": peak_equity,
        "peak_return": peak_return,
        "max_drawdown": max_drawdown,
        "worst_name_drawdown": max(name_dds) if name_dds else None,
        "win_tickers": win_tickers,
        "ticker_count": len(returns),
        "equity_curve": portfolio,
        "names": [
            {
                "ticker": part["ticker"],
                "net_pnl": part.get("net_pnl"),
                "total_return": part.get("total_return"),
                "max_drawdown": part.get("max_drawdown"),
                "trades": part.get("trades") or 0,
            }
            for part in sorted(parts, key=lambda row: str(row["ticker"]))
        ],
    }


def _empty_batch_row(
    *,
    status: str,
    sleeve: str,
    ticker: str,
    error: str | None,
) -> dict:
    return {
        "status": status,
        "sleeve": sleeve,
        "ticker": ticker,
        "tf": None,
        "bars": None,
        "from": None,
        "to": None,
        "trades": 0,
        "trade_rows": [],
        "net_pnl": None,
        "total_return": None,
        "max_drawdown": None,
        "excess_return": None,
        "oos_trades": None,
        "oos_excess_return": None,
        "capital_eligible": False,
        "evidence_score": None,
        "error": error,
    }


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
        "trade_rows": _batch_trade_rows(report),
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
    sleeve_parts: dict[str, list[dict]] = defaultdict(list)
    for sleeve in selected_sleeves:
        for ticker in selected_tickers:
            try:
                report = desk_backtest(sleeve=sleeve, ticker=ticker, env=env)
                row = _batch_row(report)
                rows.append(row)
                backtest = report.get("backtest") or {}
                summary = backtest.get("summary") or {}
                config = backtest.get("config") or {}
                initial = summary.get("initial_cash")
                if initial is None:
                    initial = config.get("initial_cash")
                sleeve_parts[sleeve].append(
                    {
                        "ticker": ticker,
                        "curve": backtest.get("equity_curve") or [],
                        "initial_cash": initial,
                        "net_pnl": row.get("net_pnl"),
                        "total_return": row.get("total_return"),
                        "max_drawdown": row.get("max_drawdown"),
                        "trades": row.get("trades") or 0,
                    }
                )
            except FileNotFoundError:
                rows.append(
                    _empty_batch_row(
                        status="skipped",
                        sleeve=sleeve,
                        ticker=ticker,
                        error="нет файла свечей",
                    )
                )
            except Exception as exc:  # noqa: BLE001 — сводка пакета fail-soft
                rows.append(
                    _empty_batch_row(
                        status="error",
                        sleeve=sleeve,
                        ticker=ticker,
                        error=str(exc) or "ошибка прогона",
                    )
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
    by_sleeve = [
        _sleeve_batch_summary(sleeve, sleeve_parts[sleeve])
        for sleeve in selected_sleeves
        if sleeve_parts.get(sleeve)
    ]
    return {
        "sleeves": selected_sleeves,
        "tickers": selected_tickers,
        "count": len(rows),
        "ok": len(ok_rows),
        "skipped": sum(1 for row in rows if row["status"] == "skipped"),
        "errors": sum(1 for row in rows if row["status"] == "error"),
        "rows": rows,
        "top": ranked[:10],
        "by_sleeve": by_sleeve,
    }
