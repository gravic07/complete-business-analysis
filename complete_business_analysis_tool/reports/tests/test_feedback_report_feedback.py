import pytest

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import Feedback


@pytest.mark.django_db
def test_feedback_report_feedback_defaults_to_empty_string():
    feedback = Feedback.objects.create(assessment=AssessmentFactory())
    assert feedback.report_feedback == ""


@pytest.mark.django_db
def test_feedback_stores_report_feedback():
    feedback = Feedback.objects.create(
        assessment=AssessmentFactory(),
        report_feedback="Needs more detail in financials.",
    )
    assert feedback.report_feedback == "Needs more detail in financials."


@pytest.mark.django_db
def test_feedback_has_no_overall_text_field():
    feedback = Feedback.objects.create(assessment=AssessmentFactory())
    assert not hasattr(feedback, "overall_text")
