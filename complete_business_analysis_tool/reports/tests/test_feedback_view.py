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
    stub = type("T", (), {"delay": staticmethod(lambda pk: None)})()
    monkeypatch.setattr(
        "complete_business_analysis_tool.reports.views.run_analysis",
        stub,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.services.run_analysis",
        stub,
    )


@pytest.mark.django_db
def test_post_overall_feedback_creates_feedback_and_redirects_to_autostart_analysis(
    monkeypatch,
):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(url, {"report_feedback": "Needs more depth overall."})

    assert response.status_code == http.HTTPStatus.FOUND
    feedback = Feedback.objects.get(assessment=assessment)
    assert feedback.report_feedback == "Needs more depth overall."
    assert not Analysis.objects.filter(assessment=assessment).exists()

    report_url = reverse("reports:report", kwargs={"pk": assessment.pk})
    assert response.url == f"{report_url}?autostart=1&feedback_id={feedback.pk}"

    generate_url = reverse("reports:generate_analysis", kwargs={"pk": assessment.pk})
    client.post(generate_url, {"feedback_id": str(feedback.pk)})

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
    response = client.post(url, {"report_feedback": ""})

    assert response.status_code == http.HTTPStatus.OK
    assert not Feedback.objects.filter(assessment=assessment).exists()
    assert not Analysis.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_submit_feedback_view_context_has_executive_summary_and_category_sections(
    monkeypatch,
):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(url, {"report_feedback": ""})

    assert response.status_code == http.HTTPStatus.OK
    assert "executive_summary" in response.context
    assert "category_sections" in response.context
    assert "sections" not in response.context


@pytest.mark.django_db
def test_post_feedback_allowed_when_analysis_active_but_autostart_does_not_duplicate_it(
    monkeypatch,
):
    _stub_task(monkeypatch)
    assessment, _ = _make_assessment_with_category()
    active_analysis = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.PENDING,
    )

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:submit_feedback", kwargs={"pk": assessment.pk})
    response = client.post(url, {"report_feedback": "Something is off."})

    assert response.status_code == http.HTTPStatus.FOUND
    feedback = Feedback.objects.get(assessment=assessment)

    generate_url = reverse("reports:generate_analysis", kwargs={"pk": assessment.pk})
    client.post(generate_url, {"feedback_id": str(feedback.pk)})

    assert Analysis.objects.filter(assessment=assessment).count() == 1
    assert Analysis.objects.get(assessment=assessment).pk == active_analysis.pk
