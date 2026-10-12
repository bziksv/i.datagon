from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.strategy.desk import desk_backtest
from app.strategy.experiments import new_experiment
from app.strategy.paper_forward import new_paper_forward_run
from worker.paper_forward import evaluate_campaign


def test_worker_only_uses_bars_after_preregistered_start(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "SBER.csv"
    path.write_text(Path("tests/fixtures/sber_daily.csv").read_text())
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    report = desk_backtest(sleeve="sma_cross", ticker="SBER")
    experiment = new_experiment(report)
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=experiment.id,
        started_at=datetime(2026, 1, 5, 12, tzinfo=UTC),
    )

    assert (
        evaluate_campaign(
            run,
            experiment,
            now=datetime(2026, 1, 5, 23, tzinfo=UTC),
        )
        is None
    )
    observation = evaluate_campaign(
        run,
        experiment,
        now=datetime(2026, 1, 9, 23, tzinfo=UTC),
    )
    assert observation is not None
    assert observation.observed_at == datetime(2026, 1, 9, tzinfo=UTC)
    assert Decimal(str(observation.strategy_equity)) > 0
    assert Decimal(str(observation.benchmark_equity)) > 0


def test_worker_rejects_campaign_when_strategy_code_changed(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "SBER.csv"
    path.write_text(Path("tests/fixtures/sber_daily.csv").read_text())
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    experiment = new_experiment(
        desk_backtest(sleeve="sma_cross", ticker="SBER")
    )
    experiment.code_hash = "0" * 64
    run = new_paper_forward_run(
        sleeve="sma_cross",
        experiment_id=experiment.id,
        started_at=datetime(2026, 1, 5, 12, tzinfo=UTC),
    )
    assert (
        evaluate_campaign(
            run,
            experiment,
            now=datetime(2026, 1, 9, 23, tzinfo=UTC),
        )
        is None
    )
