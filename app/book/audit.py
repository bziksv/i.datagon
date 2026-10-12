"""Append-only audit chain for compensating book corrections."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from app.models import AuditEvent


def _event_hash(
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload: dict,
    previous_hash: str | None,
    occurred_at: datetime,
) -> str:
    body = {
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
        "previous_hash": previous_hash,
        "occurred_at": occurred_at.isoformat(),
    }
    encoded = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def new_audit_event(
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload: dict,
    previous_hash: str | None = None,
    occurred_at: datetime | None = None,
) -> AuditEvent:
    timestamp = occurred_at or datetime.now(UTC)
    return AuditEvent(
        id=uuid4(),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=dict(payload),
        previous_hash=previous_hash,
        event_hash=_event_hash(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            previous_hash=previous_hash,
            occurred_at=timestamp,
        ),
        occurred_at=timestamp,
    )


def audit_chain_valid(rows: Sequence[AuditEvent]) -> bool:
    previous = None
    for row in sorted(rows, key=lambda item: (item.occurred_at, str(item.id))):
        if row.previous_hash != previous:
            return False
        expected = _event_hash(
            event_type=row.event_type,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            payload=row.payload,
            previous_hash=row.previous_hash,
            occurred_at=row.occurred_at,
        )
        if row.event_hash != expected:
            return False
        previous = row.event_hash
    return True


def audit_event_view(row: AuditEvent) -> dict:
    return {
        "id": str(row.id),
        "event_type": row.event_type,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "payload": row.payload,
        "previous_hash": row.previous_hash,
        "event_hash": row.event_hash,
        "occurred_at": row.occurred_at.isoformat(),
    }
