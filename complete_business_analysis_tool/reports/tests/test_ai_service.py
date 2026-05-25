from decimal import Decimal

from complete_business_analysis_tool.reports.ai_service import (
    generate_category_section,
    generate_section,
)


def test_generate_section_returns_non_empty_string():
    stub = lambda prompt: "Generated narrative about the category."  # noqa: E731
    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Very strong", "rank": 5},
        },
    ]
    result = generate_section(
        scope_label="Finance",
        answers=answers,
        category_scores={"Finance": Decimal("10.0")},
        total_score=Decimal("10.0"),
        llm_client=stub,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_section_uses_question_and_option_snapshots():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    answers = [
        {
            "question_snapshot": "Rate your marketing strategy?",
            "option_snapshot": {"text": "Excellent", "rank": 4},
        },
    ]
    generate_section(
        scope_label="Marketing",
        answers=answers,
        category_scores={},
        total_score=Decimal("4.0"),
        llm_client=capturing_client,
    )
    assert "Rate your marketing strategy?" in captured["prompt"]
    assert "Excellent" in captured["prompt"]


def test_generate_section_includes_scope_label_in_prompt():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_section(
        scope_label="Operations",
        answers=[],
        category_scores={},
        total_score=Decimal("0"),
        llm_client=capturing_client,
    )
    assert "Operations" in captured["prompt"]


def test_generate_section_includes_feedback_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_section(
        scope_label="Overall",
        answers=[],
        category_scores={},
        total_score=Decimal("0"),
        feedback_text="Focus more on cash flow.",
        llm_client=capturing_client,
    )
    assert "Focus more on cash flow." in captured["prompt"]


# --- generate_category_section ---


def test_generate_category_section_returns_non_empty_string():
    stub = lambda prompt: "Generated narrative."  # noqa: E731
    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Very strong", "rank": 5},
        },
    ]
    result = generate_category_section(answers=answers, llm_client=stub)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_category_section_prompt_contains_no_numeric_scores():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Strong", "rank": 7},
        },
    ]
    generate_category_section(answers=answers, llm_client=capturing_client)
    prompt = captured["prompt"]
    assert "score" not in prompt.lower()
    assert "7" not in prompt


def test_generate_category_section_prompt_contains_no_section_header():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_category_section(answers=[], llm_client=capturing_client)
    assert "Section:" not in captured["prompt"]


def test_generate_category_section_prompt_instructs_second_person():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_category_section(answers=[], llm_client=capturing_client)
    prompt = captured["prompt"]
    assert "second person" in prompt.lower() or "your business" in prompt.lower()


def test_generate_category_section_includes_qa_answers_in_prompt():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    answers = [
        {
            "question_snapshot": "Describe your pricing strategy.",
            "option_snapshot": {"text": "Value-based pricing", "rank": 3},
        },
    ]
    generate_category_section(answers=answers, llm_client=capturing_client)
    assert "Describe your pricing strategy." in captured["prompt"]
    assert "Value-based pricing" in captured["prompt"]


def test_generate_category_section_includes_prior_content_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_category_section(
        answers=[],
        prior_content="Your operations are currently fragmented.",
        llm_client=capturing_client,
    )
    assert "Your operations are currently fragmented." in captured["prompt"]


def test_generate_category_section_includes_feedback_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_category_section(
        answers=[],
        feedback_text="Emphasise the supply chain risks.",
        llm_client=capturing_client,
    )
    assert "Emphasise the supply chain risks." in captured["prompt"]
