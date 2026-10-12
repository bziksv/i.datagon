from collections.abc import AsyncIterator
from pathlib import Path

from app.db import get_db
from app.main import create_app
from app.strategy.desk import desk_backtest
from app.strategy.experiments import (
    experiment_fingerprint,
    new_experiment,
    result_is_intact,
)
from fastapi.testclient import TestClient


def _prepare_bars(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "SBER.csv"
    path.write_text(Path("tests/fixtures/sber_daily.csv").read_text())
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path))
    return path


def test_experiment_hashes_data_config_code_and_result(tmp_path, monkeypatch) -> None:
    path = _prepare_bars(tmp_path, monkeypatch)
    report = desk_backtest(sleeve="sma_cross", ticker="SBER")
    first = experiment_fingerprint(report)
    second = experiment_fingerprint(report)
    assert first == second
    assert all(len(value) == 64 for value in first.values())

    row = new_experiment(report)
    assert result_is_intact(row)
    row.result["bars"] = 999
    assert not result_is_intact(row)

    path.write_text(path.read_text() + "\n")
    changed = experiment_fingerprint(
        desk_backtest(sleeve="sma_cross", ticker="SBER")
    )
    assert changed["data_hash"] != first["data_hash"]


class _ExperimentSession:
    def __init__(self) -> None:
        self.row = None

    async def scalar(self, stmt):
        return self.row

    def add(self, row) -> None:
        self.row = row

    async def commit(self) -> None:
        return None

    async def refresh(self, row) -> None:
        return None

    async def get(self, model, row_id):
        if self.row is not None and self.row.id == row_id:
            return self.row
        return None


def test_backtest_experiment_api_persists_and_deduplicates(
    tmp_path,
    monkeypatch,
) -> None:
    _prepare_bars(tmp_path, monkeypatch)
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    session = _ExperimentSession()

    async def db() -> AsyncIterator[_ExperimentSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db] = db
    client = TestClient(app)
    headers = {"X-App-Token": "secret"}
    body = {"sleeve": "sma_cross", "ticker": "SBER"}

    created = client.post("/backtests", headers=headers, json=body)
    assert created.status_code == 200, created.text
    assert created.json()["deduplicated"] is False
    experiment_id = created.json()["id"]

    repeated = client.post("/backtests", headers=headers, json=body)
    assert repeated.status_code == 200
    assert repeated.json()["id"] == experiment_id
    assert repeated.json()["deduplicated"] is True

    fetched = client.get(f"/backtests/{experiment_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["result_hash"] == created.json()["result_hash"]
    trades = client.get(f"/backtests/{experiment_id}/trades", headers=headers)
    assert trades.status_code == 200
    assert isinstance(trades.json()["trades"], list)
