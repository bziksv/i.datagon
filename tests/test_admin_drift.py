from collections.abc import AsyncIterator
from decimal import Decimal

from fastapi.testclient import TestClient

from app.book.drift import drift_view
from app.db import get_db
from app.main import PUBLIC_PATHS, create_app


def test_drift_view_compares_book_and_sandbox() -> None:
    got = drift_view(Decimal("1000000"), Decimal("998000"))
    assert got["ledger_cash"] == 1000000.0
    assert got["sandbox_cash"] == 998000.0
    assert got["drift"] == 2000.0
    assert got["alert"] is True


def test_admin_drift_requires_token(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert "/admin/drift" not in PUBLIC_PATHS
    assert client.get("/admin/drift").status_code == 401


def test_admin_drift_with_token_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get(
        "/admin/drift",
        headers={"X-App-Token": "secret"},
        params={"sandbox_cash": "1000000"},
    )
    assert response.status_code == 503


class _EmptySession:
    async def scalars(self, _stmt) -> list:
        return []


async def _empty_db() -> AsyncIterator[_EmptySession]:
    yield _EmptySession()


def test_admin_drift_with_token(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()
    app.dependency_overrides[get_db] = _empty_db
    client = TestClient(app)
    response = client.get(
        "/admin/drift",
        headers={"X-App-Token": "secret"},
        params={"sandbox_cash": "1000000"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sandbox_cash"] == 1000000.0
    assert body["ledger_cash"] == 0.0
    assert "drift" in body
