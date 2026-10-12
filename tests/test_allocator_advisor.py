import inspect
from datetime import UTC, datetime, timedelta

from app.agent import allocator
from app.agent.allocator import advise_weights
from app.agent.proposals import STATUS_PROPOSED
from app.agent.schemas import ProposeWeights
from app.alloc.capital import allocate
from app.alloc.view import ACTIVE_SLEEVES


def test_advisor_writes_propose_weights() -> None:
    before = allocate(ACTIVE_SLEEVES)
    run, proposal = advise_weights(enabled=True)
    after = allocate(ACTIVE_SLEEVES)
    assert run.role == "allocator_advisor"
    assert proposal.kind == "weights"
    assert proposal.status == STATUS_PROPOSED
    parsed = ProposeWeights.model_validate(proposal.payload)
    assert sum(row.weight for row in parsed.weights) == 1
    assert {row.sleeve: row.weight for row in parsed.weights} == {
        **{sleeve: 0.0 for sleeve in ACTIVE_SLEEVES},
        "cash": 1.0,
    }
    assert before == after


def test_advisor_allocates_only_to_oos_qualified_sleeves() -> None:
    evidence = {
        ACTIVE_SLEEVES[0]: {
            "trades": 8,
            "excess_return": 0.04,
            "insufficient_statistics": False,
        },
        ACTIVE_SLEEVES[1]: {
            "trades": 2,
            "excess_return": 0.20,
            "insufficient_statistics": True,
        },
    }
    _, proposal = advise_weights(enabled=True, evidence=evidence)
    weights = {
        row["sleeve"]: row["weight"] for row in proposal.payload["weights"]
    }
    assert weights == {
        ACTIVE_SLEEVES[0]: 0.3,
        **{sleeve: 0.0 for sleeve in ACTIVE_SLEEVES[1:]},
        "cash": 0.7,
    }


def test_advisor_does_not_apply_weights() -> None:
    source = inspect.getsource(allocator)
    assert "new_proposal" in source
    assert "propose_weights" in source.lower() or "ProposeWeights" in source
    assert "set_status" not in source
    assert "approved" not in source
    assert "allocate(" not in source


def test_advisor_uses_risk_budgets_for_qualified_sleeves() -> None:
    evidence = {
        ACTIVE_SLEEVES[0]: {"capital_eligible": True},
        ACTIVE_SLEEVES[1]: {"capital_eligible": True},
    }
    returns = {
        ACTIVE_SLEEVES[0]: [0.01, -0.01, 0.01, -0.01],
        ACTIVE_SLEEVES[1]: [0.05, -0.05, 0.05, -0.05],
    }
    _, proposal = advise_weights(
        enabled=True,
        evidence=evidence,
        returns=returns,
    )
    weights = {
        row["sleeve"]: row["weight"] for row in proposal.payload["weights"]
    }
    assert weights[ACTIVE_SLEEVES[0]] > weights[ACTIVE_SLEEVES[1]]
    assert weights["cash"] == 0.5


def test_advisor_observes_rebalance_cooldown() -> None:
    run, proposal = advise_weights(
        enabled=True,
        last_rebalance_at=datetime.now(UTC) - timedelta(days=1),
    )
    assert proposal is None
    assert "cooldown" in run.output
