from complete_business_analysis_tool.reports.ai_service import generate_roadmap


def _stub_roadmap_client(prompt: str) -> dict:
    return {
        "months": [
            {
                "goals": ["g1", "g2", "g3", "g4", "g5"],
                "action_items": ["a1", "a2", "a3", "a4", "a5"],
                "challenges": ["c1", "c2", "c3", "c4", "c5"],
            }
            for _ in range(12)
        ],
        "potential_challenges": ["pc1", "pc2", "pc3", "pc4"],
        "post_implementation_outcomes": ["pio1", "pio2", "pio3", "pio4"],
        "closing_reflections": ["cr1", "cr2"],
    }


def _capturing_client():
    captured = {}

    def client(prompt: str) -> dict:
        captured["prompt"] = prompt
        return _stub_roadmap_client(prompt)

    return client, captured


def test_generate_roadmap_returns_12_months_with_5_items_each():
    result = generate_roadmap(
        category_recommendations={"Finance": ["Rec 1", "Rec 2"]},
        category_sections={"Finance": "Overview:\nSome text."},
        business_name="Acme Corp",
        llm_client=_stub_roadmap_client,
    )
    assert len(result["months"]) == 12  # noqa: PLR2004
    for month in result["months"]:
        assert len(month["goals"]) == 5  # noqa: PLR2004
        assert len(month["action_items"]) == 5  # noqa: PLR2004
        assert len(month["challenges"]) == 5  # noqa: PLR2004
        assert all(isinstance(item, str) for item in month["goals"])
        assert all(isinstance(item, str) for item in month["action_items"])
        assert all(isinstance(item, str) for item in month["challenges"])


def test_generate_roadmap_returns_non_empty_supplementary_lists():
    result = generate_roadmap(
        category_recommendations={"Finance": ["Rec 1"]},
        category_sections={"Finance": "Overview:\nSome text."},
        business_name="Acme Corp",
        llm_client=_stub_roadmap_client,
    )
    assert len(result["potential_challenges"]) > 0
    assert all(isinstance(item, str) for item in result["potential_challenges"])
    assert len(result["post_implementation_outcomes"]) > 0
    assert all(isinstance(item, str) for item in result["post_implementation_outcomes"])
    assert len(result["closing_reflections"]) > 0
    assert all(isinstance(item, str) for item in result["closing_reflections"])


def test_generate_roadmap_prompt_includes_category_recommendations():
    client, captured = _capturing_client()
    generate_roadmap(
        category_recommendations={
            "Finance": ["Invest in forecasting tools.", "Reduce overhead costs."],
            "Marketing": ["Improve SEO strategy.", "Launch email campaigns."],
        },
        category_sections={
            "Finance": "Overview:\nText.",
            "Marketing": "Overview:\nText.",
        },
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "Invest in forecasting tools." in captured["prompt"]
    assert "Reduce overhead costs." in captured["prompt"]
    assert "Improve SEO strategy." in captured["prompt"]
    assert "Launch email campaigns." in captured["prompt"]


def test_generate_roadmap_prompt_includes_category_sections():
    client, captured = _capturing_client()
    generate_roadmap(
        category_recommendations={"Finance": ["Rec 1."]},
        category_sections={
            "Finance": "Overview:\nCash flow is constrained.\n\n"
            "Path Forward:\nPrioritize reserves.",
        },
        business_name="Acme Corp",
        llm_client=client,
    )
    assert "Cash flow is constrained." in captured["prompt"]
    assert "Prioritize reserves." in captured["prompt"]


def test_generate_roadmap_prompt_instructs_third_person_with_business_name():
    client, captured = _capturing_client()
    generate_roadmap(
        category_recommendations={"Finance": ["Rec 1."]},
        category_sections={"Finance": "Overview:\nText."},
        business_name="Pinnacle Logistics",
        llm_client=client,
    )
    assert "third person" in captured["prompt"].lower()
    assert "Pinnacle Logistics" in captured["prompt"]
