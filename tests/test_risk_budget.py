from decimal import Decimal

from app.alloc.risk_budget import risk_budget_weights


def test_lower_volatility_receives_larger_risk_budget() -> None:
    weights = risk_budget_weights(
        ["stable", "volatile"],
        {
            "stable": [0.01, -0.01, 0.01, -0.01],
            "volatile": [0.05, -0.05, 0.05, -0.05],
        },
    )
    assert sum(weights.values(), Decimal("0")) == Decimal("1")
    assert weights["stable"] > weights["volatile"]


def test_positive_correlation_penalizes_otherwise_similar_sleeve() -> None:
    weights = risk_budget_weights(
        ["diversifier", "crowded", "peer"],
        {
            "diversifier": [0.01, -0.01, 0.01, -0.01, 0.01],
            "crowded": [0.01, 0.02, -0.01, -0.02, 0.01],
            "peer": [0.01, 0.02, -0.01, -0.02, 0.01],
        },
    )
    assert weights["diversifier"] > weights["crowded"]


def test_missing_return_history_falls_back_to_equal_budget() -> None:
    weights = risk_budget_weights(["a", "b"], {})
    assert weights == {"a": Decimal("0.5"), "b": Decimal("0.5")}
