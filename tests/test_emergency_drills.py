from datetime import UTC, datetime

from app.ops.emergency import emergency_drills


def test_all_emergency_drills_pass_with_healthy_restarted_worker() -> None:
    result = emergency_drills(
        worker_alive=True,
        now=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert result["gate"] == "G4"
    assert result["passed"] is True
    assert all(check["passed"] for check in result["checks"])


def test_worker_failure_keeps_g4_blocked() -> None:
    result = emergency_drills(
        worker_alive=False,
        now=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert result["passed"] is False
    checks = {row["code"]: row["passed"] for row in result["checks"]}
    assert checks["worker_restart_recovered"] is False
