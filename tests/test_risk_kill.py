from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.main import create_app
from app.models import Flag
from app.risk.kill import KILLED, apply_kill, gate_kill, is_killed, kill_view
from fastapi.testclient import TestClient


def _order():
    return draft_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="market",
            client_order_id="c-kill-1",
        ),
        sleeve="sma_cross",
    )


def test_kill_flag_denies_all_new_orders() -> None:
    flags: list[Flag] = []
    apply_kill(flags, True)
    assert is_killed(flags) is True
    assert kill_view(flags) == {"killed": True}

    denied = gate_kill(_order(), flags)
    assert denied.status == STATUS_REJECTED
    assert denied.raw["reject_reason"] == KILLED

    apply_kill(flags, False)
    assert is_killed(flags) is False
    assert gate_kill(_order(), flags).status == STATUS_NEW


def test_kill_unkill_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.post("/kill").status_code == 401
    assert client.post("/unkill").status_code == 401


def test_kill_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.post("/kill", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
