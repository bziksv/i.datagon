from decimal import Decimal
from uuid import uuid4

from app.book.ledger import apply_deposit
from app.book.portfolio import portfolio_from_book, portfolio_view
from app.main import create_app
from app.models import Position
from fastapi.testclient import TestClient


def test_portfolio_json_shape() -> None:
    deposit, cash = apply_deposit([])
    assert deposit is not None
    position = Position(
        sleeve="manual",
        instrument_id=uuid4(),
        qty=10,
        avg_price=Decimal("100"),
    )
    view = portfolio_from_book([deposit], [position])
    assert view["cash"] == 1000000.0
    assert view["vault"] == 0.0
    assert view["positions"][0]["qty"] == 10
    assert view["positions"][0]["avg_price"] == 100.0
    assert view["equity"] == 1001000.0
    assert set(portfolio_view(cash=cash, positions=[position])) == {
        "cash",
        "vault",
        "positions",
        "equity",
    }


def test_portfolio_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/portfolio")
    assert response.status_code == 401


def test_portfolio_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/portfolio", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
