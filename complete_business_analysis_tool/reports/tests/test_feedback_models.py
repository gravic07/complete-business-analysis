from http import HTTPStatus

import pytest
from django.db.models import ProtectedError
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    CategoryFactory,
)
from complete_business_analysis_tool.reports.factories import FeedbackFactory
from complete_business_analysis_tool.reports.models import CategoryFeedback, Feedback
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_feedback_requires_only_assessment_and_created_by():
    assessment = AssessmentFactory.create()
    feedback = Feedback.objects.create(
        assessment=assessment,
        created_by=assessment.created_by,
    )
    assert feedback.pk is not None
    assert feedback.report_feedback == ""


@pytest.mark.django_db
def test_feedback_stores_report_feedback():
    feedback = FeedbackFactory.create(
        report_feedback="Needs more detail in financials.",
    )
    assert feedback.report_feedback == "Needs more detail in financials."


@pytest.mark.django_db
def test_category_feedback_links_feedback_and_category():
    category = CategoryFactory.create()
    feedback = FeedbackFactory.create()
    cf = CategoryFeedback.objects.create(
        feedback=feedback,
        category=category,
        text="Marketing is weak.",
    )
    assert cf.pk is not None
    assert cf.feedback == feedback
    assert cf.category == category
    assert cf.text == "Marketing is weak."


@pytest.mark.django_db
def test_deleting_user_who_submitted_feedback_is_refused():
    user = UserFactory.create()
    FeedbackFactory.create(created_by=user, assessment=AssessmentFactory.create())

    with pytest.raises(ProtectedError):
        user.delete()


@pytest.mark.django_db
def test_admin_feedback_changelist_shows_created_by(admin_client):
    FeedbackFactory.create()

    response = admin_client.get(reverse("admin:reports_feedback_changelist"))

    assert response.status_code == HTTPStatus.OK
    assert "column-created_by" in response.content.decode()
