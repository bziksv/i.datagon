import time
from pathlib import Path

from app.ops.candle_pull_job import gap_tickers_from_coverage, start_fill, status_view


def test_gap_tickers_skips_ready() -> None:
    got = gap_tickers_from_coverage(
        {
            "items": [
                {"ticker": "SBER", "status": "ready"},
                {"ticker": "GAZP", "status": "missing"},
                {"ticker": "LKOH", "status": "short"},
            ]
        }
    )
    assert got == ["GAZP", "LKOH"]


def test_start_fill_runs_in_background(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "fill.json"
    monkeypatch.setenv("CANDLE_FILL_JOB_PATH", str(state))
    seen: list[str] = []

    def fake_pull(ticker: str, *, tf: str, days: int) -> int:
        seen.append(ticker)
        time.sleep(0.05)
        return 10

    # reset module thread state between tests
    import app.ops.candle_pull_job as job

    with job._lock:
        job._thread = None
        job._cancel.clear()

    started = start_fill(
        ["AAA", "BBB"],
        tf="1d",
        path=state,
        pull=fake_pull,
    )
    assert started["status"] == "running"
    assert started["total"] == 2

    deadline = time.time() + 3
    final = None
    while time.time() < deadline:
        final = status_view(state)
        if final["status"] == "done":
            break
        time.sleep(0.05)

    assert final is not None
    assert final["status"] == "done"
    assert seen == ["AAA", "BBB"]
    assert set(final["done"]) == {"AAA", "BBB"}


def test_fill_endpoints(tmp_path: Path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    state = tmp_path / "fill.json"
    monkeypatch.setenv("CANDLE_FILL_JOB_PATH", str(state))
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x")

    import app.ops.candle_pull_job as job

    with job._lock:
        job._thread = None
        job._cancel.clear()

    def fake_pull(ticker: str, *, tf: str, days: int) -> int:
        return 7

    monkeypatch.setattr(job, "pull_one", fake_pull)

    client = TestClient(create_app())
    headers = {"X-App-Token": "secret"}
    empty = client.get("/desk/candles/fill", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["status"] in {"idle", "done", "error", "cancelled"}

    started = client.post(
        "/desk/candles/fill",
        headers=headers,
        json={"tf": "1d", "tickers": ["SBER", "GAZP"]},
    )
    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "running"
    assert body["total"] == 2

    st = body
    deadline = time.time() + 3
    while time.time() < deadline:
        st = client.get("/desk/candles/fill", headers=headers).json()
        if st["status"] == "done":
            break
        time.sleep(0.05)
    assert st["status"] == "done"
    assert len(st["done"]) == 2
