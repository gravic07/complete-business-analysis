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
        "potential_challenges": "pc1\n\npc2\n\npc3\n\npc4",
        "post_implementation_outcomes": "pio1\n\npio2\n\npio3\n\npio4",
        "closing_reflections": "cr1\n\ncr2",
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


def test_generate_roadmap_returns_prose_strings_for_supplementary_fields():
    result = generate_roadmap(
        category_recommendations={"Finance": ["Rec 1"]},
        category_sections={"Finance": "Overview:\nSome text."},
        business_name="Acme Corp",
        llm_client=_stub_roadmap_client,
    )
    assert isinstance(result["potential_challenges"], str)
    assert len(result["potential_challenges"]) > 0
    assert isinstance(result["post_implementation_outcomes"], str)
    assert len(result["post_implementation_outcomes"]) > 0
    assert isinstance(result["closing_reflections"], str)
    assert len(result["closing_reflections"]) > 0


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


def test_generate_roadmap_prompt_instructs_prose_paragraphs():
    client, captured = _capturing_client()
    generate_roadmap(
        category_recommendations={"Finance": ["Rec 1."]},
        category_sections={"Finance": "Overview:\nText."},
        business_name="Acme Corp",
        llm_client=client,
    )
    prompt = captured["prompt"]
    assert "3-4 paragraphs" in prompt
    assert "4-6 paragraphs" in prompt
    assert "\\n\\n" in prompt or r"\n\n" in prompt


def test_generate_roadmap_prompt_forbids_bullets_in_prose_fields():
    client, captured = _capturing_client()
    generate_roadmap(
        category_recommendations={"Finance": ["Rec 1."]},
        category_sections={"Finance": "Overview:\nText."},
        business_name="Acme Corp",
        llm_client=client,
    )
    prompt = captured["prompt"].lower()
    assert "bullet" in prompt or "no list" in prompt or "no bullet" in prompt
