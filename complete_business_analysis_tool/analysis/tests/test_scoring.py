"""Pure-function tests for the scoring engine. No database needed."""

from decimal import Decimal

from complete_business_analysis_tool.analysis.scoring import compute_scores


def test_max_possible_score_reflects_highest_rank_per_question():
    answers = [
        {"category_id": "cat-1", "rank": 1, "weight": Decimal("2.0000"), "max_rank": 5},
        {"category_id": "cat-1", "rank": 3, "weight": Decimal("1.0000"), "max_rank": 4},
    ]
    result = compute_scores(answers)
    # max = 5x2.0 + 4x1.0 = 10 + 4 = 14
    assert result.category_max_scores["cat-1"] == Decimal("14.0")
    assert result.total_max == Decimal("14.0")


def test_answers_across_two_categories_produce_correct_breakdown():
    answers = [
        {"category_id": "cat-A", "rank": 4, "weight": Decimal("1.0000"), "max_rank": 5},
        {"category_id": "cat-B", "rank": 2, "weight": Decimal("3.0000"), "max_rank": 5},
    ]
    result = compute_scores(answers)
    assert result.category_scores["cat-A"] == Decimal("4.0")
    assert result.category_scores["cat-B"] == Decimal("6.0")
    assert result.total == Decimal("10.0")


def test_single_category_score_is_rank_times_weight():
    answers = [
        {"category_id": "cat-1", "rank": 3, "weight": Decimal("2.0000"), "max_rank": 5},
        {"category_id": "cat-1", "rank": 2, "weight": Decimal("1.5000"), "max_rank": 5},
    ]
    result = compute_scores(answers)
    # 3x2.0 + 2x1.5 = 6.0 + 3.0 = 9.0
    assert result.category_scores["cat-1"] == Decimal("9.0")
    assert result.total == Decimal("9.0")
