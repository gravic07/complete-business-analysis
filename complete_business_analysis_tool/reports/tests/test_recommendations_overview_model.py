import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import RecommendationsOverview


@pytest.mark.django_db
def test_recommendations_overview_can_be_created():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    overview = RecommendationsOverview.objects.create(
        analysis=analysis,
        content="Action-focused recommendations overview.",
    )
    assert overview.pk is not None
    assert overview.content == "Action-focused recommendations overview."


@pytest.mark.django_db
def test_recommendations_overview_unique_per_analysis():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    RecommendationsOverview.objects.create(analysis=analysis, content="first")
    with pytest.raises(IntegrityError):
        RecommendationsOverview.objects.create(analysis=analysis, content="second")
