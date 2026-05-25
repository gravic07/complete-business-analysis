"""
Scoring engine — pure function, no ORM calls.

Each answer dict must have:
  category_id  — str, groups answers into categories
  rank         — int, the selected option's rank
  weight       — Decimal, the selected option's weight
  max_rank     — int, the highest rank available for that question
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ScoreResult:
    category_scores: dict[str, Decimal] = field(default_factory=dict)
    category_max_scores: dict[str, Decimal] = field(default_factory=dict)
    total: Decimal = Decimal("0")
    total_max: Decimal = Decimal("0")


def compute_scores(answers: list[dict]) -> ScoreResult:
    result = ScoreResult()
    for answer in answers:
        cat = answer["category_id"]
        score = Decimal(answer["rank"]) * answer["weight"]
        max_score = Decimal(answer["max_rank"]) * answer["weight"]
        result.category_scores[cat] = (
            result.category_scores.get(cat, Decimal("0")) + score
        )
        result.category_max_scores[cat] = (
            result.category_max_scores.get(cat, Decimal("0")) + max_score
        )
    result.total = sum(result.category_scores.values(), Decimal("0"))
    result.total_max = sum(result.category_max_scores.values(), Decimal("0"))
    return result
