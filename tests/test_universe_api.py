from uuid import uuid4

from app.main import create_app
from app.models import Instrument, UniverseMember
from app.universe.view import universe_view
from fastapi.testclient import TestClient


def test_universe_lists_only_active() -> None:
    live = Instrument(
        id=uuid4(),
        ticker="SBER",
        figi="FIGI",
        uid="uid",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )
    dead = Instrument(
        id=uuid4(),
        ticker="GAZP",
        figi="FIGI2",
        uid="uid2",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )
    members = [
        UniverseMember(
            instrument_id=live.id, reason="tradable,rub,lot,liquid", active=True
        ),
        UniverseMember(instrument_id=dead.id, reason="not_tradable", active=False),
    ]
    view = universe_view(members, [live, dead], limit=30)
    assert [row["ticker"] for row in view["members"]] == ["SBER", "GAZP"]
    assert view["members"][0]["reason"] == "tradable,rub,lot,liquid"
    assert view["members"][0]["active"] is True
    assert view["members"][1]["active"] is False
    assert view["count"] == 1
    assert view["limit"] == 30


def test_universe_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/universe")
    assert response.status_code == 401


def test_universe_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/universe", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
