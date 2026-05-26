from decimal import Decimal

from complete_business_analysis_tool.reports.ai_service import (
    generate_category_section,
    generate_executive_summary,
)

# --- generate_category_section ---


def test_generate_category_section_returns_dict_with_three_keys():
    def stub(_prompt: str) -> str:
        return (
            '{"overview": "Overview text.", '
            '"impact": "Impact text.", '
            '"path_forward": "Path."}'
        )

    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Very strong", "rank": 5},
        },
    ]
    result = generate_category_section(
        answers=answers,
        business_name="Acme Corp",
        llm_client=stub,
    )
    assert isinstance(result, dict)
    assert isinstance(result["overview"], str)
    assert result["overview"]
    assert isinstance(result["impact"], str)
    assert result["impact"]
    assert isinstance(result["path_forward"], str)
    assert result["path_forward"]


def test_generate_category_section_includes_prior_overview_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        prior_overview="Your cash flow is currently strong.",
        llm_client=capturing_client,
    )
    assert "Your cash flow is currently strong." in captured["prompt"]


def test_generate_category_section_includes_prior_impact_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        prior_impact="This limits your growth potential.",
        llm_client=capturing_client,
    )
    assert "This limits your growth potential." in captured["prompt"]


def test_generate_category_section_includes_prior_path_forward_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        prior_path_forward="You should invest in automation.",
        llm_client=capturing_client,
    )
    assert "You should invest in automation." in captured["prompt"]


def test_generate_category_section_prompt_specifies_five_to_eight_sentences():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "5-8 sentences" in captured["prompt"]


def test_generate_category_section_prompt_instructs_json_with_three_keys():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt = captured["prompt"]
    assert '"overview"' in prompt
    assert '"impact"' in prompt
    assert '"path_forward"' in prompt
    assert "json" in prompt.lower()


def test_generate_category_section_prompt_contains_no_numeric_scores():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    answers = [
        {
            "question_snapshot": "How is your cash flow?",
            "option_snapshot": {"text": "Strong", "rank": 7},
        },
    ]
    generate_category_section(
        answers=answers,
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt = captured["prompt"]
    assert "score" not in prompt.lower()
    assert "7" not in prompt


def test_generate_category_section_prompt_contains_no_section_header():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "Section:" not in captured["prompt"]


def test_generate_category_section_prompt_instructs_third_person():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt = captured["prompt"]
    assert "third person" in prompt.lower() or "Acme Corp" in prompt


def test_generate_category_section_includes_qa_answers_in_prompt():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    answers = [
        {
            "question_snapshot": "Describe your pricing strategy.",
            "option_snapshot": {"text": "Value-based pricing", "rank": 3},
        },
    ]
    generate_category_section(
        answers=answers,
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "Describe your pricing strategy." in captured["prompt"]
    assert "Value-based pricing" in captured["prompt"]


def test_generate_category_section_includes_feedback_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"overview": "o", "impact": "i", "path_forward": "p"}'

    generate_category_section(
        answers=[],
        business_name="Acme Corp",
        feedback_text="Emphasise the supply chain risks.",
        llm_client=capturing_client,
    )
    assert "Emphasise the supply chain risks." in captured["prompt"]


# --- generate_executive_summary ---


def test_generate_executive_summary_returns_non_empty_string():
    stub = lambda prompt: "Overall synthesis narrative."  # noqa: E731
    result = generate_executive_summary(
        category_sections={"Finance": "Your cash flow is strong."},
        category_scores={"Finance": Decimal("8.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=stub,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_executive_summary_includes_prior_content_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={},
        category_max_scores={},
        business_name="Acme Corp",
        prior_content="Your business has strong fundamentals.",
        llm_client=capturing_client,
    )
    assert "Your business has strong fundamentals." in captured["prompt"]


def test_generate_executive_summary_includes_feedback_when_provided():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={},
        category_max_scores={},
        business_name="Acme Corp",
        feedback_text="Focus more on operational dependencies.",
        llm_client=capturing_client,
    )
    assert "Focus more on operational dependencies." in captured["prompt"]


def test_generate_executive_summary_prompt_instructs_third_person():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={},
        category_max_scores={},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt_lower = captured["prompt"].lower()
    assert "third person" in prompt_lower or "Acme Corp" in captured["prompt"]


def test_generate_executive_summary_prompt_does_not_contain_sequencing_language():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={},
        category_max_scores={},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt_lower = captured["prompt"].lower()
    assert "sequencing" not in prompt_lower
    assert "simultaneously" not in prompt_lower
    assert "low-hanging fruit" not in prompt_lower
    assert "urgent" not in prompt_lower


def test_generate_executive_summary_prompt_instructs_four_to_five_paragraph_synthesis():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={},
        category_max_scores={},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "4-5 paragraph" in captured["prompt"]


def test_generate_executive_summary_prompt_prohibits_citing_raw_scores():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={},
        category_scores={"Finance": Decimal("6.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    prompt_lower = captured["prompt"].lower()
    assert "do not cite" in prompt_lower or "not cite raw" in prompt_lower


def test_generate_executive_summary_prompt_contains_category_scores_with_max():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={"Finance": "Text."},
        category_scores={"Finance": Decimal("7.5")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "Finance" in captured["prompt"]
    assert "7.5 / 10.0" in captured["prompt"]


def test_generate_executive_summary_prompt_contains_all_category_section_texts():
    captured = {}

    def capturing_client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Response"

    generate_executive_summary(
        category_sections={
            "Finance": "Your cash flow is strong.",
            "Marketing": "Your brand awareness needs work.",
        },
        category_scores={"Finance": Decimal("8.0"), "Marketing": Decimal("4.0")},
        category_max_scores={"Finance": Decimal("10.0"), "Marketing": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=capturing_client,
    )
    assert "Your cash flow is strong." in captured["prompt"]
    assert "Your brand awareness needs work." in captured["prompt"]
