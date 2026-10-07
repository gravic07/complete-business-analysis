import pytest

from complete_business_analysis_tool.reports.factories import FeedbackFactory


@pytest.mark.django_db
def test_feedback_report_feedback_defaults_to_empty_string():
    feedback = FeedbackFactory.create()
    assert feedback.report_feedback == ""


@pytest.mark.django_db
def test_feedback_stores_report_feedback():
    feedback = FeedbackFactory.create(
        report_feedback="Needs more detail in financials.",
    )
    assert feedback.report_feedback == "Needs more detail in financials."


@pytest.mark.django_db
def test_feedback_has_no_overall_text_field():
    feedback = FeedbackFactory.create()
    assert not hasattr(feedback, "overall_text")
