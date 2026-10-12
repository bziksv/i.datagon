"""Воспроизводимые backtest-эксперименты с проверяемыми отпечатками."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from app.models import BacktestExperiment


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _code_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def experiment_fingerprint(report: dict) -> dict[str, str]:
    path = Path(str(report["path"]))
    data_hash = _sha256(path.read_bytes())
    config = {
        "sleeve": report["sleeve"],
        "ticker": report["ticker"],
        "tf": report["tf"],
        "backtest": report["backtest"]["config"],
        "walk_forward": {
            "method": (report.get("walk_forward") or {}).get("method"),
            "train_bars": (report.get("walk_forward") or {}).get("train_bars"),
            "test_bars": (report.get("walk_forward") or {}).get("test_bars"),
        },
    }
    result_hash = _sha256(_canonical(report))
    return {
        "data_hash": data_hash,
        "config_hash": _sha256(_canonical(config)),
        "code_hash": _code_hash(),
        "result_hash": result_hash,
    }


def new_experiment(report: dict) -> BacktestExperiment:
    fingerprint = experiment_fingerprint(report)
    return BacktestExperiment(
        id=uuid4(),
        sleeve=str(report["sleeve"]),
        ticker=str(report["ticker"]),
        result=dict(report),
        **fingerprint,
    )


def experiment_view(row: BacktestExperiment, *, include_result: bool = True) -> dict:
    body = {
        "id": str(row.id),
        "sleeve": row.sleeve,
        "ticker": row.ticker,
        "data_hash": row.data_hash,
        "config_hash": row.config_hash,
        "code_hash": row.code_hash,
        "result_hash": row.result_hash,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    if include_result:
        body["result"] = row.result
    return body


def result_is_intact(row: BacktestExperiment) -> bool:
    return _sha256(_canonical(row.result)) == row.result_hash
