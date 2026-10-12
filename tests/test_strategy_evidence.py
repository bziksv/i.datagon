from app.strategy.evidence import VERSION, strategy_evidence


def _report(*, excess: float, trades: int, drawdown: float = 0.05) -> dict:
    return {
        "backtest": {"summary": {"net_pnl": 9000, "costs": 1000}},
        "walk_forward": {
            "oos_summary": {
                "excess_return": excess,
                "trades": trades,
                "max_drawdown": drawdown,
                "folds": 3,
            }
        },
    }


def test_evidence_score_is_explainable_and_bounded() -> None:
    result = strategy_evidence(_report(excess=0.05, trades=20))
    assert result["version"] == VERSION
    assert 0 <= result["score"] <= 100
    assert sum(
        component["points"] for component in result["components"].values()
    ) == result["score"]
    assert result["components"]["oos_edge"]["points"] == 30
    assert result["components"]["sample"]["points"] == 20
    assert result["capital_eligible"] is False
    assert "paper_forward_missing" in result["blockers"]


def test_positive_paper_forward_can_make_strong_evidence_credible() -> None:
    result = strategy_evidence(
        _report(excess=0.05, trades=20),
        paper_forward={"days": 30, "excess_return": 0.01},
    )
    assert result["score"] >= 70
    assert result["rating"] == "credible"
    assert result["capital_eligible"] is True
    assert result["blockers"] == []


def test_weak_oos_is_fail_closed() -> None:
    result = strategy_evidence(_report(excess=-0.01, trades=2, drawdown=0.40))
    assert result["rating"] == "insufficient"
    assert result["capital_eligible"] is False
    assert "fewer_than_5_oos_trades" in result["blockers"]
    assert "non_positive_oos_excess" in result["blockers"]
