from decimal import Decimal

from complete_business_analysis_tool.reports.ai_service import (
    generate_recommendations_overview,
)


def _capturing_client():
    captured = {}

    def client(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Action-focused recommendations overview narrative."

    return client, captured


def test_generate_recommendations_overview_returns_non_empty_string():
    stub = lambda prompt: "Recommendations overview text."  # noqa: E731
    result = generate_recommendations_overview(
        category_recommendations={"Finance": ["Rec 1", "Rec 2"]},
        category_scores={"Finance": Decimal("8.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=stub,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_recommendations_overview_prompt_includes_all_cat_recommendation_text():
    client, captured = _capturing_client()
    generate_recommendations_overview(
        category_recommendations={
            "Finance": ["Invest in forecasting tools.", "Reduce overhead costs."],
            "Marketing": ["Improve SEO strategy.", "Launch email campaigns."],
        },
        category_scores={"Finance": Decimal("8.0"), "Marketing": Decimal("4.0")},
        category_max_scores={"Finance": Decimal("10.0"), "Marketing": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "Invest in forecasting tools." in captured["prompt"]
    assert "Reduce overhead costs." in captured["prompt"]
    assert "Improve SEO strategy." in captured["prompt"]
    assert "Launch email campaigns." in captured["prompt"]


def test_generate_recommendations_overview_prompt_instructs_third_person():
    client, captured = _capturing_client()
    generate_recommendations_overview(
        category_recommendations={"Finance": ["Do X."]},
        category_scores={"Finance": Decimal("8.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "third person" in captured["prompt"].lower()
    assert "Acme Corp" in captured["prompt"]


def test_generate_recommendations_overview_prompt_prohibits_citing_raw_scores():
    client, captured = _capturing_client()
    generate_recommendations_overview(
        category_recommendations={"Finance": ["Do X."]},
        category_scores={"Finance": Decimal("6.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        llm_client=client,
    )
    prompt_lower = captured["prompt"].lower()
    assert "do not cite" in prompt_lower or "not cite raw" in prompt_lower


def test_generate_recommendations_overview_prompt_includes_prior_content_when_provided():
    client, captured = _capturing_client()
    generate_recommendations_overview(
        category_recommendations={"Finance": ["Do X."]},
        category_scores={"Finance": Decimal("8.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        prior_content="Prior overview narrative.",
        llm_client=client,
    )
    assert "Prior overview narrative." in captured["prompt"]


def test_generate_recommendations_overview_prompt_includes_feedback_when_provided():
    client, captured = _capturing_client()
    generate_recommendations_overview(
        category_recommendations={"Finance": ["Do X."]},
        category_scores={"Finance": Decimal("8.0")},
        category_max_scores={"Finance": Decimal("10.0")},
        business_name="Acme Corp",
        feedback_text="Focus on operational priorities.",
        llm_client=client,
    )
    assert "Focus on operational priorities." in captured["prompt"]
