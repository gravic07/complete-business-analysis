import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    CategoryFactory,
)
from complete_business_analysis_tool.reports.models import CategorySection


@pytest.mark.django_db
def test_category_section_can_be_created():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    category = CategoryFactory.create()
    section = CategorySection.objects.create(
        analysis=analysis,
        category=category,
        overview="Overview text",
        impact="Impact text",
        path_forward="Path forward text",
    )
    assert section.pk is not None
    assert section.overview == "Overview text"
    assert section.impact == "Impact text"
    assert section.path_forward == "Path forward text"


@pytest.mark.django_db
def test_category_section_category_is_required():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    with pytest.raises(IntegrityError):
        CategorySection.objects.create(
            analysis=analysis,
            category=None,
            overview="text",
            impact="text",
            path_forward="text",
        )


@pytest.mark.django_db
def test_category_section_unique_per_analysis_category():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    category = CategoryFactory.create()
    CategorySection.objects.create(
        analysis=analysis,
        category=category,
        overview="first",
        impact="first",
        path_forward="first",
    )
    with pytest.raises(IntegrityError):
        CategorySection.objects.create(
            analysis=analysis,
            category=category,
            overview="second",
            impact="second",
            path_forward="second",
        )
