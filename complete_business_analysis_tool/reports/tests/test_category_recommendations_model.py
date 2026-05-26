import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    CategoryFactory,
)
from complete_business_analysis_tool.reports.models import CategoryRecommendations


@pytest.mark.django_db
def test_category_recommendations_can_be_created():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    category = CategoryFactory()

    rec = CategoryRecommendations.objects.create(
        analysis=analysis,
        category=category,
        recommendations=["rec 1", "rec 2", "rec 3", "rec 4", "rec 5", "rec 6", "rec 7"],
    )

    assert rec.pk is not None
    assert rec.recommendations == [
        "rec 1",
        "rec 2",
        "rec 3",
        "rec 4",
        "rec 5",
        "rec 6",
        "rec 7",
    ]


@pytest.mark.django_db
def test_category_recommendations_category_is_required():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())

    with pytest.raises(IntegrityError):
        CategoryRecommendations.objects.create(
            analysis=analysis,
            category=None,
            recommendations=[],
        )


@pytest.mark.django_db
def test_category_recommendations_unique_per_analysis_category():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    category = CategoryFactory()
    recs = ["r1", "r2", "r3", "r4", "r5", "r6", "r7"]

    CategoryRecommendations.objects.create(
        analysis=analysis,
        category=category,
        recommendations=recs,
    )

    with pytest.raises(IntegrityError):
        CategoryRecommendations.objects.create(
            analysis=analysis,
            category=category,
            recommendations=recs,
        )
