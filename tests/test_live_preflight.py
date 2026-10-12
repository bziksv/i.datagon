from app.ops.live_preflight import live_preflight


def test_live_preflight_is_blocked_even_when_paper_gates_pass() -> None:
    report = live_preflight(
        {"G1": True, "G2": True, "G3": True, "G4": True},
        live_env_enabled=False,
    )
    assert report["status"] == "blocked"
    assert report["live_eligible"] is False
    assert report["activation_supported"] is False
    assert "independent_security_audit" in report["blockers"]
    assert "explicit_owner_decision" in report["blockers"]
    assert "live_activation_path" in report["blockers"]


def test_enabling_live_env_adds_a_fail_closed_blocker() -> None:
    report = live_preflight(
        {"G1": True, "G2": True, "G3": True, "G4": True},
        live_env_enabled=True,
    )
    assert "paper_build" in report["blockers"]
    paper = next(
        row for row in report["checks"] if row["code"] == "paper_build"
    )
    assert paper["passed"] is False


def test_unfinished_paper_gate_is_visible() -> None:
    report = live_preflight(
        {"G1": True, "G2": True, "G3": False, "G4": True},
        live_env_enabled=False,
    )
    assert "g3_passed" in report["blockers"]
