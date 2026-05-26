from decimal import Decimal

from complete_business_analysis_tool.reports.ai_service import (
    generate_category_recommendations,
)


def _stub_client(prompt: str) -> list:
    return ["rec 1", "rec 2", "rec 3", "rec 4", "rec 5", "rec 6", "rec 7"]


def _capturing_client():
    captured = {}

    def client(prompt: str) -> list:
        captured["prompt"] = prompt
        return ["r1", "r2", "r3", "r4", "r5", "r6", "r7"]

    return client, captured


def test_generate_category_recommendations_returns_seven_non_empty_strings():
    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Very strong", "rank": 5},
        },
    ]
    result = generate_category_recommendations(
        answers=answers,
        section_text="Overview: Strong fundamentals.",
        score=Decimal("8.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        llm_client=_stub_client,
    )
    assert isinstance(result, list)
    expected_recommendation_cnt = 7
    assert len(result) == expected_recommendation_cnt
    assert all(isinstance(r, str) and r for r in result)


def test_generate_category_recommendations_prompt_includes_qa_answers():
    client, captured = _capturing_client()
    generate_category_recommendations(
        answers=[
            {
                "question_snapshot": "Describe your pricing strategy.",
                "option_snapshot": {"text": "Value-based pricing", "rank": 3},
            },
        ],
        section_text="Overview text.",
        score=Decimal("5.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "Describe your pricing strategy." in captured["prompt"]
    assert "Value-based pricing" in captured["prompt"]


def test_generate_category_recommendations_prompt_includes_section_text():
    client, captured = _capturing_client()
    generate_category_recommendations(
        answers=[],
        section_text="Overview: The finance function is underdeveloped.",
        score=Decimal("4.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "The finance function is underdeveloped." in captured["prompt"]


def test_generate_category_recommendations_prompt_instructs_third_person():
    client, captured = _capturing_client()
    generate_category_recommendations(
        answers=[],
        section_text="",
        score=Decimal("5.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        llm_client=client,
    )
    prompt = captured["prompt"]
    assert "third person" in prompt.lower() or "Acme Corp" in prompt


def test_generate_category_recommendations_prompt_does_not_instruct_emitting_raw_scores():
    client, captured = _capturing_client()
    generate_category_recommendations(
        answers=[],
        section_text="",
        score=Decimal("6.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        llm_client=client,
    )
    prompt_lower = captured["prompt"].lower()
    assert "do not cite raw" in prompt_lower or "not cite raw numeric" in prompt_lower


def test_generate_category_recommendations_prompt_includes_prior_recommendations():
    client, captured = _capturing_client()
    prior = ["Invest in staff training.", "Review pricing quarterly."]
    generate_category_recommendations(
        answers=[],
        section_text="",
        score=Decimal("5.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        prior_recommendations=prior,
        llm_client=client,
    )
    assert "Invest in staff training." in captured["prompt"]
    assert "Review pricing quarterly." in captured["prompt"]


def test_generate_category_recommendations_prompt_includes_feedback_text():
    client, captured = _capturing_client()
    generate_category_recommendations(
        answers=[],
        section_text="",
        score=Decimal("5.0"),
        max_score=Decimal("10.0"),
        business_name="Acme Corp",
        feedback_text="Focus on operational efficiency.",
        llm_client=client,
    )
    assert "Focus on operational efficiency." in captured["prompt"]
