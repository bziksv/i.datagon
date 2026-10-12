"""Персональный контур: скор фундамента и кандидаты (не ИК)."""

from app.advisory.score import score_fundamental
from app.advisory.screener import propose_from_scores, rank_candidates
from app.advisory.view import fundamentals_view, recommendations_view

__all__ = [
    "fundamentals_view",
    "propose_from_scores",
    "rank_candidates",
    "recommendations_view",
    "score_fundamental",
]
