import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    CategoryFactory,
)
from complete_business_analysis_tool.reports.models import ReportSection


@pytest.mark.django_db
def test_report_section_can_be_created_with_category():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    category = CategoryFactory()
    section = ReportSection.objects.create(
        analysis=analysis,
        category=category,
        content="Some text",
    )
    assert section.pk is not None


@pytest.mark.django_db
def test_overall_report_section_has_null_category():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    section = ReportSection.objects.create(
        analysis=analysis,
        category=None,
        content="Overall text",
    )
    assert section.category is None


@pytest.mark.django_db
def test_analysis_category_pair_is_unique():
    analysis = Analysis.objects.create(assessment=AssessmentFactory())
    category = CategoryFactory()
    ReportSection.objects.create(analysis=analysis, category=category, content="First")
    with pytest.raises(IntegrityError):
        ReportSection.objects.create(
            analysis=analysis,
            category=category,
            content="Second",
        )
