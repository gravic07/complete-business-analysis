import pytest

from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    CategoryFactory,
)
from complete_business_analysis_tool.reports.models import CategoryFeedback, Feedback


@pytest.mark.django_db
def test_feedback_requires_only_assessment():
    assessment = AssessmentFactory.create()
    feedback = Feedback.objects.create(assessment=assessment)
    assert feedback.pk is not None
    assert feedback.report_feedback == ""


@pytest.mark.django_db
def test_feedback_stores_report_feedback():
    assessment = AssessmentFactory.create()
    feedback = Feedback.objects.create(
        assessment=assessment,
        report_feedback="Needs more detail in financials.",
    )
    assert feedback.report_feedback == "Needs more detail in financials."


@pytest.mark.django_db
def test_category_feedback_links_feedback_and_category():
    assessment = AssessmentFactory.create()
    category = CategoryFactory.create()
    feedback = Feedback.objects.create(assessment=assessment)
    cf = CategoryFeedback.objects.create(
        feedback=feedback,
        category=category,
        text="Marketing is weak.",
    )
    assert cf.pk is not None
    assert cf.feedback == feedback
    assert cf.category == category
    assert cf.text == "Marketing is weak."
