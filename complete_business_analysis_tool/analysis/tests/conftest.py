import pytest


@pytest.fixture(autouse=True)
def _stub_ai_functions(monkeypatch) -> None:
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "", "impact": "", "path_forward": ""},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_recommendations",
        lambda **kwargs: ["r"] * 7,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_recommendations_overview",
        lambda **kwargs: "",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_roadmap",
        lambda **kwargs: {
            "months": [
                {"goals": ["g"], "action_items": ["a"], "challenges": ["c"]}
                for _ in range(12)
            ],
            "potential_challenges": "p",
            "post_implementation_outcomes": "o",
            "closing_reflections": "r",
        },
    )
