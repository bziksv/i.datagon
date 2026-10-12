from decimal import Decimal
from pathlib import Path

from app.alloc.plan import allocation_plan
from app.main import create_app
from app.risk.params_store import load_name_share, save_name_share
from fastapi.testclient import TestClient


def test_name_share_store_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("RISK_PARAMS_PATH", str(tmp_path / "risk.json"))
    save_name_share(Decimal("0.05"))
    assert load_name_share() == Decimal("0.05")
    plan = allocation_plan(
        equity=Decimal("1000000"),
        sleeves=["sma_cross"],
        weights={"sma_cross": Decimal("1")},
        example_price=Decimal("250"),
    )
    assert plan["name_share"] == 0.05
    assert plan["sleeves"][0]["name_budget"] == 20000.0  # 1e6*0.4*1 * 0.05


def test_allocation_risk_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("RISK_PARAMS_PATH", str(tmp_path / "risk.json"))
    client = TestClient(create_app())
    headers = {"X-App-Token": "secret"}
    got = client.get("/allocation/risk", headers=headers)
    assert got.status_code == 200
    put = client.put(
        "/allocation/risk",
        headers=headers,
        json={"name_share": 0.08},
    )
    assert put.status_code == 200, put.text
    body = put.json()
    assert body["name_share"] == 0.08
    assert body["max_concurrent_names"] == 12
    assert load_name_share() == Decimal("0.08")


def test_allocation_risk_rejects_out_of_range(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("RISK_PARAMS_PATH", str(tmp_path / "risk.json"))
    client = TestClient(create_app())
    headers = {"X-App-Token": "secret"}
    assert (
        client.put(
            "/allocation/risk",
            headers=headers,
            json={"name_share": 0.005},
        ).status_code
        == 422
    )


def test_ledger_deposit_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.post("/ledger/deposit", json={"amount": 1000000}).status_code == 401


def test_cabin_deposit_and_name_share_ui() -> None:
    js = Path("web/cabin.js").read_text()
    assert 'id: "settings"' in js
    assert "renderSettings" in js
    assert "settings-capital" in js
    assert 'renderCapitalSettingsForm("settings")' in js
    assert "-deposit-amount" in js
    assert "-name-share" in js
    assert "strategies-capital-setup" in js
    assert 'apiPost("/ledger/deposit"' in js
    assert 'apiPut("/allocation/risk"' in js
    assert "макс. на одну бумагу" in js
    primary = js.split("MOBILE_PRIMARY_IDS")[1].split("]")[0]
    assert "settings" in primary
    assert "strategies-guide" in js
    assert "strategies-desk-verdict" in js
