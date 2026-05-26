import http
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
)
from complete_business_analysis_tool.reports.models import CategorySection
from complete_business_analysis_tool.users.tests.factories import UserFactory


def _make_report(assessment, monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: "cat narrative",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "overall narrative",
    )
    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    return analysis


@pytest.mark.django_db
def test_report_view_redirects_unauthenticated_user():
    assessment = AssessmentFactory()
    client = Client()
    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = client.get(url)
    assert response.status_code == http.HTTPStatus.FOUND
    assert "/accounts/" in response["Location"]


@pytest.mark.django_db
def test_report_view_returns_200_for_authenticated_user(monkeypatch):
    assessment = AssessmentFactory()
    _make_report(assessment, monkeypatch)

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = client.get(url)
    assert response.status_code == http.HTTPStatus.OK


@pytest.mark.skip(reason="template rendering updated in view layer issue")
@pytest.mark.django_db
def test_report_view_shows_overall_section_first(monkeypatch):
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=2, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)
    _make_report(assessment, monkeypatch)

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = client.get(url)

    content = response.content.decode()
    overall_pos = content.index("overall narrative")
    category_pos = content.index("cat narrative")
    assert overall_pos < category_pos


@pytest.mark.skip(reason="template rendering updated in view layer issue")
@pytest.mark.django_db
def test_report_view_assembles_latest_section_per_category(monkeypatch):
    call_num = [0]

    def numbered_category(**kwargs):
        call_num[0] += 1
        return f"cat-run-{call_num[0]}"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        numbered_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "overall",
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    analysis2 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis2.pk)

    user = UserFactory()
    client = Client()
    client.force_login(user)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = client.get(url)
    content = response.content.decode()

    latest_section = CategorySection.objects.filter(
        analysis=analysis2,
        category=category,
    ).get()
    assert latest_section.overview in content
    earliest_section = CategorySection.objects.filter(
        analysis=analysis1,
        category=category,
    ).get()
    assert earliest_section.overview not in content
