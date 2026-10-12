from uuid import UUID

from app.agent import store
from app.agent.proposals import new_proposal


def test_proposals_survive_reload(tmp_path, monkeypatch) -> None:
    path = tmp_path / "proposals.json"
    monkeypatch.setenv("PROPOSALS_PATH", str(path))
    previous = dict(store._STORE)
    try:
        row = store.remember(new_proposal("order", {"ticker": "SBER"}))
        assert path.is_file()
        store._STORE.clear()
        store._load()
        loaded = store.get_proposal(row.id)
        assert loaded is not None
        assert loaded.payload["ticker"] == "SBER"
        assert isinstance(loaded.id, UUID)
    finally:
        store._STORE.clear()
        store._STORE.update(previous)
