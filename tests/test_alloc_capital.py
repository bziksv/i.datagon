from decimal import Decimal

from app.alloc.view import ACTIVE_SLEEVES, allocation_view
from app.alloc.capital import allocate, sleeve_capital
from app.main import create_app
from app.risk.sleeve import DEFAULT_SLEEVE_SHARE
from app.strategy.donchian import SLEEVE as DONCHIAN
from app.strategy.sma import SLEEVE
from fastapi.testclient import TestClient


def test_one_sleeve_gets_full_cap_within_101() -> None:
    weights = allocate([SLEEVE])
    assert weights == {SLEEVE: Decimal("1")}
    capital = sleeve_capital(Decimal("1000000"), weight=weights[SLEEVE])
    assert capital == Decimal("400000")


def test_active_sleeves_equal_weight_within_101() -> None:
    weights = allocate(ACTIVE_SLEEVES)
    assert len(ACTIVE_SLEEVES) == 5
    share = Decimal("1") / Decimal(len(ACTIVE_SLEEVES))
    assert weights[SLEEVE] == share
    assert weights[DONCHIAN] == share
    assert sum(weights.values()) == Decimal("1")
    for name in ACTIVE_SLEEVES:
        capital = sleeve_capital(Decimal("1000000"), weight=weights[name])
        assert capital == Decimal("80000")
        assert capital <= Decimal("1000000") * DEFAULT_SLEEVE_SHARE


def test_allocation_weights_in_view(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SLEEVE_WEIGHTS_PATH", str(tmp_path / "missing.json"))
    view = allocation_view(ACTIVE_SLEEVES, equity=Decimal("1000000"))
    assert view["sleeve_share"] == 0.4
    assert view["equity"] == 1000000.0
    assert [row["sleeve"] for row in view["sleeves"]] == [
        "sma_cross",
        "donchian_breakout",
        "rsi_reversion",
        "ema_scalp",
        "overnight_bounce",
    ]
    assert [row["weight"] for row in view["sleeves"]] == [
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
    ]
    assert [row["capital"] for row in view["sleeves"]] == [
        80000.0,
        80000.0,
        80000.0,
        80000.0,
        80000.0,
    ]


def test_allocation_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/allocation").status_code == 401


def test_allocation_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/allocation", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
