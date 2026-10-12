from datetime import UTC, datetime
from uuid import uuid4

from app.models import Fundamental, Instrument, UniverseMember
from app.settings import Settings
from app.universe.reason import inclusion_reason, ReasonFacts
from worker.universe import mark_fundamentals


def _instrument(ticker: str) -> Instrument:
    return Instrument(
        id=uuid4(),
        ticker=ticker,
        figi=None,
        uid=None,
        lot=1,
        currency="rub",
        class_code="TQBR",
    )


def _snap(ticker: str, pe: float | None) -> Fundamental:
    return Fundamental(
        ticker=ticker,
        asset_uid=f"asset-{ticker.lower()}",
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        pe_ratio_ttm=pe,
        price_to_book_ttm=1.0,
        eps_ttm=10.0,
        market_capitalization=1.0,
        raw={},
    )


def test_flag_off_leaves_members() -> None:
    inst = _instrument("SBER")
    member = UniverseMember(instrument_id=inst.id, reason="dump", active=True)
    mark_fundamentals([member], [inst], [], enabled=False)
    assert member.active is True


def test_flag_on_uses_snapshot() -> None:
    ok = _instrument("SBER")
    missing = _instrument("GAZP")
    loss = _instrument("VTBR")
    members = [
        UniverseMember(instrument_id=ok.id, reason="dump", active=True),
        UniverseMember(instrument_id=missing.id, reason="dump", active=True),
        UniverseMember(instrument_id=loss.id, reason="dump", active=True),
    ]
    mark_fundamentals(
        members,
        [ok, missing, loss],
        [_snap("SBER", 5.5), _snap("VTBR", -1.0)],
        enabled=True,
    )
    assert members[0].active is True
    assert members[1].active is False
    assert members[2].active is False


def test_config_disables_fundamentals(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "t")
    monkeypatch.setenv("APP_AUTH_TOKEN", "a")
    monkeypatch.setenv("UNIVERSE_FUNDAMENTALS", "0")
    settings = Settings()
    assert settings.universe_fundamentals is False
    assert inclusion_reason(ReasonFacts(True, True, True, True, False)) == (
        "weak_fundamental"
    )
