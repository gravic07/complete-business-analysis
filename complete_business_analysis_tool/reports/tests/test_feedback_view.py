import http
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
)
from complete_business_analysis_tool.reports.models import CategoryFeedback, Feedback
from complete_business_analysis_tool.users.tests.factories import UserFactory


def _make_assessment_with_category():
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)
    return assessment, category


def _stub_task(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.reports.views.run_analysis",
        type("T", (), {"delay": staticmethod(lambda pk: None)})(),
    )


@pytest.mark.django_db
def test_post_overall_feedback_creates_feedback_and_pending_analysis(monkeypatch):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(url, {"overall_text": "Needs more depth overall."})

    assert response.status_code == http.HTTPStatus.FOUND
    feedback = Feedback.objects.get(assessment=assessment)
    assert feedback.report_feedback == "Needs more depth overall."
    assert Analysis.objects.filter(
        assessment=assessment,
        feedback=feedback,
        status=Analysis.Status.PENDING,
    ).exists()


@pytest.mark.django_db
def test_post_category_feedback_creates_category_feedback_record(monkeypatch):
    _stub_task(monkeypatch)
    assessment, category = _make_assessment_with_category()

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(
        url,
        {f"category_{category.pk}": "Marketing section is weak."},
    )

    assert response.status_code == http.HTTPStatus.FOUND
    feedback = Feedback.objects.get(assessment=assessment)
    assert feedback.report_feedback == ""
    cf = CategoryFeedback.objects.get(feedback=feedback)
    assert cf.category == category
    assert cf.text == "Marketing section is weak."


@pytest.mark.django_db
def test_post_empty_feedback_is_rejected(monkeypatch):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(
        url,
        {
            "overall_text": "",
        },
    )

    assert response.status_code == http.HTTPStatus.OK
    assert not Feedback.objects.filter(assessment=assessment).exists()
    assert not Analysis.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_post_feedback_rejected_when_analysis_already_active(monkeypatch):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()
    Analysis.objects.create(assessment=assessment, status=Analysis.Status.PENDING)

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(url, {"overall_text": "Something is off."})

    assert response.status_code == http.HTTPStatus.OK
    assert not Feedback.objects.filter(assessment=assessment).exists()
    assert Analysis.objects.filter(assessment=assessment).count() == 1
