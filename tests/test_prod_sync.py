from __future__ import annotations

from app.main import create_app
from app.ops import prod_sync
from fastapi.testclient import TestClient

SRC = "root@example.org:/srv/app"


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PROD_SYNC", raising=False)
    assert not prod_sync.enabled()
    assert not prod_sync.blocks_write("/work/enable")
    assert prod_sync.start_background() is None
    assert prod_sync.view()["enabled"] is False


def test_blocks_data_and_desk_writes(monkeypatch):
    monkeypatch.setenv("PROD_SYNC", SRC)
    for path in (
        "/work/enable",
        "/work/order",
        "/desk/candles/pull",
        "/fundamentals/refresh",
    ):
        assert prod_sync.blocks_write(path), path
    for path in ("/work/probe", "/backtests/run", "/kill"):
        assert not prod_sync.blocks_write(path), path


def test_split_and_interval(monkeypatch):
    assert prod_sync._split(SRC + "/") == ("root@example.org", "/srv/app")
    monkeypatch.setenv("PROD_SYNC_INTERVAL_SEC", "5")
    assert prod_sync.interval_sec() == 60
    monkeypatch.setenv("PROD_SYNC_INTERVAL_SEC", "x")
    assert prod_sync.interval_sec() == prod_sync.DEFAULT_INTERVAL_SEC


def test_rsync_filters_mirror_only_listed_paths():
    rules = prod_sync.rsync_filters()
    assert rules[0] == "--exclude=*.tmp"
    assert rules[-1] == "--exclude=*"
    assert "--include=/candles/***" in rules
    assert "--include=/work_desks/***" in rules
    assert "--include=/logs/" in rules
    assert rules.index("--include=/logs/") < rules.index(
        "--include=/logs/candle-refresh.beat"
    )
    assert not any("candles_m1/" in rule or "certs" in rule for rule in rules)


def test_view_reads_state(monkeypatch, tmp_path):
    monkeypatch.setenv("PROD_SYNC", SRC)
    state = tmp_path / "prod-sync.json"
    prod_sync.write_state(
        {"ok": True, "last_at": "2026-10-21T15:00:00+00:00", "sec": 20}, state
    )
    monkeypatch.setattr(prod_sync, "STATE_PATH", state)
    view = prod_sync.view()
    assert view["enabled"] and view["ok"]
    assert view["source"] == "root@example.org"
    assert "/srv/app" not in str(view)


def test_api_refuses_writes_in_mirror(monkeypatch):
    monkeypatch.setenv("PROD_SYNC", SRC)
    monkeypatch.setattr(prod_sync, "start_background", lambda: None)
    with TestClient(create_app()) as client:
        res = client.post("/work/enable", json={})
        assert res.status_code == 409
        assert "зеркало прода" in res.text
        assert client.post("/desk/candles/pull", json={}).status_code == 409
