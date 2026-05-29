import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import Roadmap


@pytest.mark.django_db
def test_roadmap_can_be_created():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    roadmap = Roadmap.objects.create(
        analysis=analysis,
        months=[
            {
                "goals": ["Goal 1"],
                "action_items": ["Action 1"],
                "challenges": ["Challenge 1"],
            },
        ]
        * 12,
        potential_challenges=["Challenge paragraph one.", "Challenge paragraph two."],
        post_implementation_outcomes=["Outcome paragraph one."],
        closing_reflections=["Reflection paragraph one."],
    )
    assert roadmap.pk is not None
    expected_month_cnt = 12
    assert len(roadmap.months) == expected_month_cnt
    assert roadmap.potential_challenges == [
        "Challenge paragraph one.",
        "Challenge paragraph two.",
    ]
    assert roadmap.post_implementation_outcomes == ["Outcome paragraph one."]
    assert roadmap.closing_reflections == ["Reflection paragraph one."]


@pytest.mark.django_db
def test_roadmap_unique_per_analysis():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    Roadmap.objects.create(
        analysis=analysis,
        months=[],
        potential_challenges=[],
        post_implementation_outcomes=[],
        closing_reflections=[],
    )
    with pytest.raises(IntegrityError):
        Roadmap.objects.create(
            analysis=analysis,
            months=[],
            potential_challenges=[],
            post_implementation_outcomes=[],
            closing_reflections=[],
        )
