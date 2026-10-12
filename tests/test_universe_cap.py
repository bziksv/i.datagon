from decimal import Decimal
from uuid import uuid4

from app.models import UniverseMember
from app.settings import Settings
from app.universe.cap import DEFAULT_UNIVERSE_MAX, resolve_universe_max
from worker.universe import cap_universe


def test_sieve_respects_universe_max() -> None:
    members = [
        UniverseMember(instrument_id=uuid4(), reason="dump", active=True)
        for _ in range(20)
    ]
    scores = {row.instrument_id: Decimal(i) for i, row in enumerate(members)}
    cap_universe(members, scores, limit=15)
    active = [row for row in members if row.active]
    assert len(active) == 15
    assert members[-1].active is True
    assert members[0].active is False


def test_config_raises_cap_sieve_stays(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "t")
    monkeypatch.setenv("APP_AUTH_TOKEN", "a")
    monkeypatch.setenv("UNIVERSE_MAX", "30")
    settings = Settings()
    limit = resolve_universe_max(settings.universe_max)
    assert limit == DEFAULT_UNIVERSE_MAX == 30
    members = [
        UniverseMember(instrument_id=uuid4(), reason="dump", active=True)
        for _ in range(40)
    ]
    cap_universe(members, None, limit=limit)
    active = [row for row in members if row.active]
    assert len(active) == 30
    assert len(active) < len(members)
    assert resolve_universe_max(0) == DEFAULT_UNIVERSE_MAX
    assert resolve_universe_max(-5) == DEFAULT_UNIVERSE_MAX
