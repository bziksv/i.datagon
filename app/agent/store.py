"""Память предложений. Пишем на диск, если PROPOSALS_PATH задан и доступен."""

import json
import os
from pathlib import Path
from uuid import UUID

from app.models import AgentProposal

_STORE: dict[UUID, AgentProposal] = {}
DEFAULT_PROPOSALS_PATH = "/var/www/i_datagon_ru_usr/data/proposals.json"


def _store_path() -> Path | None:
    raw = os.environ.get("PROPOSALS_PATH", DEFAULT_PROPOSALS_PATH)
    if not raw:
        return None
    return Path(raw)


def _row_to_dict(row: AgentProposal) -> dict:
    return {
        "id": str(row.id),
        "kind": row.kind,
        "payload": row.payload,
        "status": row.status,
    }


def _row_from_dict(data: dict) -> AgentProposal:
    return AgentProposal(
        id=UUID(data["id"]),
        kind=data["kind"],
        payload=data.get("payload") or {},
        status=data["status"],
    )


def _save() -> None:
    path = _store_path()
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                [_row_to_dict(row) for row in _STORE.values()],
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
    except OSError:
        return


def _load() -> None:
    path = _store_path()
    if path is None or not path.is_file():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, list):
        return
    for item in raw:
        row = _row_from_dict(item)
        _STORE[row.id] = row


_load()


def remember(row: AgentProposal) -> AgentProposal:
    _STORE[row.id] = row
    _save()
    return row


def get_proposal(proposal_id: UUID) -> AgentProposal | None:
    return _STORE.get(proposal_id)


def list_proposals() -> list[AgentProposal]:
    return list(_STORE.values())


def proposal_view(
    row: AgentProposal,
    *,
    order: dict | None = None,
    weights: dict | None = None,
) -> dict:
    body = {
        "id": str(row.id),
        "kind": row.kind,
        "status": row.status,
        "payload": row.payload,
    }
    if order is not None:
        body["order"] = order
    if weights is not None:
        body["weights"] = weights
    return body
