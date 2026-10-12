"""Append prospective paper-forward observations from newly closed bars."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.db import get_sessionmaker
from app.models import (
    BacktestExperiment,
    PaperForwardObservation,
    PaperForwardRun,
)
from app.strategy.backtest import BacktestConfig, load_bars, run_backtest
from app.strategy.desk import strategy_for
from app.strategy.experiments import current_strategy_code_hash, result_is_intact
from app.strategy.paper_forward import new_observation
from sqlalchemy import select


def _backtest_config(experiment: BacktestExperiment) -> BacktestConfig:
    config = (experiment.result.get("backtest") or {}).get("config") or {}
    return BacktestConfig(
        initial_cash=Decimal(str(config["initial_cash"])),
        position_share=Decimal(str(config["position_share"])),
        commission_bps=Decimal(str(config["commission_bps"])),
        slippage_bps=Decimal(str(config["slippage_bps"])),
        lot=int(config["lot"]),
        periods_per_year=(
            6552 if str(experiment.result.get("tf")) == "15m" else 252
        ),
    )


def evaluate_campaign(
    run: PaperForwardRun,
    experiment: BacktestExperiment,
    *,
    now: datetime,
) -> PaperForwardObservation | None:
    if (
        not result_is_intact(experiment)
        or experiment.code_hash != current_strategy_code_hash()
    ):
        return None
    path = str(experiment.result.get("path") or "")
    if not path:
        return None
    bars = load_bars(Path(path))
    evaluation_start = next(
        (
            index
            for index, bar in enumerate(bars)
            if bar.ts > run.started_at and bar.ts <= now
        ),
        None,
    )
    if evaluation_start is None:
        return None
    eligible_bars = [bar for bar in bars if bar.ts <= now]
    if evaluation_start >= len(eligible_bars):
        return None
    result = run_backtest(
        strategy_for(run.sleeve),
        experiment.ticker,
        eligible_bars,
        config=_backtest_config(experiment),
        evaluation_start=evaluation_start,
    )
    summary = result["summary"]
    initial_cash = Decimal(str(summary["initial_cash"]))
    strategy_equity = Decimal(str(summary["final_equity"]))
    benchmark_equity = initial_cash * (
        Decimal("1") + Decimal(str(summary["benchmark_return"]))
    )
    return new_observation(
        run,
        strategy_equity=strategy_equity,
        benchmark_equity=benchmark_equity,
        observed_at=eligible_bars[-1].ts,
    )


async def refresh_paper_forward(*, now: datetime | None = None) -> int:
    """Persist at most one point per campaign and newly available bar."""
    observed_at = now or datetime.now(UTC)
    maker = get_sessionmaker()
    saved = 0
    async with maker() as session:
        runs = list(await session.scalars(select(PaperForwardRun)))
        for run in runs:
            experiment = await session.get(BacktestExperiment, run.experiment_id)
            if experiment is None:
                continue
            observation = evaluate_campaign(
                run,
                experiment,
                now=observed_at,
            )
            if observation is None:
                continue
            duplicate = await session.scalar(
                select(PaperForwardObservation).where(
                    PaperForwardObservation.run_id == run.id,
                    PaperForwardObservation.observed_at
                    == observation.observed_at,
                )
            )
            if duplicate is not None:
                continue
            session.add(observation)
            saved += 1
        if saved:
            await session.commit()
    return saved
