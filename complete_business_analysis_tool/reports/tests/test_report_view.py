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
from complete_business_analysis_tool.reports.models import (
    CategorySection,
    RecommendationsOverview,
)
from complete_business_analysis_tool.users.tests.factories import UserFactory


def _make_assessment_with_category():
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)
    return assessment, category


def _make_report(assessment, monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "cat overview",
            "impact": "cat impact",
            "path_forward": "cat path",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall narrative",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks"
        ".generate_category_recommendations",
        lambda **kwargs: ["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks"
        ".generate_recommendations_overview",
        lambda **kwargs: "recommendations overview narrative",
    )
    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    return analysis


def _authed_client(user=None):
    c = Client()
    c.force_login(user or UserFactory())
    return c


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
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)
    assert response.status_code == http.HTTPStatus.OK


@pytest.mark.django_db
def test_report_view_context_has_executive_summary_and_category_sections(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert "executive_summary" in response.context
    assert "category_sections" in response.context
    assert "sections" not in response.context


@pytest.mark.django_db
def test_report_view_executive_summary_none_when_no_analysis(monkeypatch):
    assessment = AssessmentFactory()

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert response.status_code == http.HTTPStatus.OK
    assert response.context["executive_summary"] is None
    assert response.context["category_sections"] == []


@pytest.mark.django_db
def test_report_view_renders_executive_summary_first(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)
    content = response.content.decode()

    exec_pos = content.index("overall narrative")
    cat_pos = content.index("cat overview")
    assert exec_pos < cat_pos


@pytest.mark.django_db
def test_report_view_renders_category_subheadings(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "Overview" in content
    assert "Impact" in content
    assert "Path Forward" in content


@pytest.mark.django_db
def test_report_view_shows_latest_section_per_category(monkeypatch):
    call_num = [0]

    def numbered_category(**kwargs):
        call_num[0] += 1
        return {"overview": f"cat-run-{call_num[0]}", "impact": "", "path_forward": ""}

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        numbered_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_recommendations",
        lambda **kwargs: ["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_recommendations_overview",
        lambda **kwargs: "overview",
    )

    assessment, category = _make_assessment_with_category()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    analysis2 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis2.pk)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    latest = CategorySection.objects.get(analysis=analysis2, category=category)
    earliest = CategorySection.objects.get(analysis=analysis1, category=category)
    assert latest.overview in content
    assert earliest.overview not in content


@pytest.mark.django_db
def test_report_view_context_has_category_recommendations(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert "category_recommendations" in response.context
    recs = response.context["category_recommendations"]
    assert len(recs) == 1
    assert recs[0].recommendations == ["r1", "r2", "r3", "r4", "r5", "r6", "r7"]


@pytest.mark.django_db
def test_report_view_context_has_recommendations_overview(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert "recommendations_overview" in response.context
    overview = response.context["recommendations_overview"]
    assert isinstance(overview, RecommendationsOverview)
    assert overview.content == "recommendations overview narrative"


@pytest.mark.django_db
def test_report_view_recommendations_overview_none_when_no_analysis():
    assessment = AssessmentFactory()

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert response.context["recommendations_overview"] is None


@pytest.mark.django_db
def test_report_view_renders_recommendations_overview_before_category_lists(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    overview_pos = content.index("recommendations overview narrative")
    rec_pos = content.index("r1")
    assert overview_pos < rec_pos


@pytest.mark.django_db
def test_report_view_does_not_render_overview_content_when_overview_is_none(
    monkeypatch,
):
    assessment, _ = _make_assessment_with_category()

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "o", "impact": "i", "path_forward": "p"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_recommendations",
        lambda **kwargs: ["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_recommendations_overview",
        lambda **kwargs: "overview text",
    )
    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    RecommendationsOverview.objects.filter(analysis=analysis).delete()

    url = reverse("reports:report", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "overview text" not in content
