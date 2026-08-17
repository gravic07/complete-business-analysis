import pytest
from django.db import IntegrityError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import ExecutiveSummary


@pytest.mark.django_db
def test_executive_summary_can_be_created():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    summary = ExecutiveSummary.objects.create(
        analysis=analysis,
        content="Overall synthesis text.",
    )
    assert summary.pk is not None
    assert summary.content == "Overall synthesis text."


@pytest.mark.django_db
def test_executive_summary_unique_per_analysis():
    analysis = Analysis.objects.create(assessment=AssessmentFactory.create())
    ExecutiveSummary.objects.create(analysis=analysis, content="first")
    with pytest.raises(IntegrityError):
        ExecutiveSummary.objects.create(analysis=analysis, content="second")
