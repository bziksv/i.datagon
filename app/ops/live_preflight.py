"""Fail-closed evidence package for a future, separate live decision."""

from __future__ import annotations

from collections.abc import Mapping


def live_preflight(
    admission: Mapping[str, bool],
    *,
    live_env_enabled: bool,
) -> dict:
    checks = [
        {
            "code": "paper_build",
            "passed": not live_env_enabled,
            "required": True,
            "explanation": "Current build must remain paper-only.",
        },
        *[
            {
                "code": f"{gate.lower()}_passed",
                "passed": bool(admission.get(gate, False)),
                "required": True,
                "explanation": f"{gate} admission prerequisite.",
            }
            for gate in ("G1", "G2", "G3", "G4")
        ],
        {
            "code": "independent_security_audit",
            "passed": False,
            "required": True,
            "explanation": "Must be completed outside this implementation.",
        },
        {
            "code": "legal_and_regulatory_review",
            "passed": False,
            "required": True,
            "explanation": "Jurisdiction and operating model require review.",
        },
        {
            "code": "broker_execution_audit",
            "passed": False,
            "required": True,
            "explanation": "Live order, cancel, fill and reconciliation audit.",
        },
        {
            "code": "explicit_owner_decision",
            "passed": False,
            "required": True,
            "explanation": "No implicit or automatic live activation.",
        },
        {
            "code": "live_activation_path",
            "passed": False,
            "required": True,
            "explanation": "This repository intentionally has no live path.",
        },
    ]
    blockers = [row["code"] for row in checks if not row["passed"]]
    return {
        "gate": "G5",
        "status": "blocked",
        "passed": False,
        "live_eligible": False,
        "activation_supported": False,
        "checks": checks,
        "blockers": blockers,
    }
