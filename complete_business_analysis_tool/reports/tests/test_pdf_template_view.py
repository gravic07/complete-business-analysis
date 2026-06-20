# ruff: noqa: PLR2004

import http
from decimal import Decimal

import pytest
from django.core.signing import TimestampSigner
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
from complete_business_analysis_tool.users.tests.factories import UserFactory


def _signed_token(assessment_pk):
    return TimestampSigner().sign(str(assessment_pk))


def _make_assessment_with_category(category_name="Finance"):
    category = CategoryFactory(name=category_name)
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
        "complete_business_analysis_tool.analysis.tasks.generate_category_recommendations",
        lambda **kwargs: ["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_recommendations_overview",
        lambda **kwargs: "recommendations overview narrative",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_roadmap",
        lambda **kwargs: {
            "months": [
                {
                    "goals": [f"goal {i}" for i in range(1, 6)],
                    "action_items": [f"action {i}" for i in range(1, 6)],
                    "challenges": [f"challenge {i}" for i in range(1, 6)],
                }
                for _ in range(12)
            ],
            "potential_challenges": "potential challenge 1\n\npotential challenge 2",
            "post_implementation_outcomes": "outcome 1\n\noutcome 2",
            "closing_reflections": "reflection 1\n\nreflection 2",
        },
    )
    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    return analysis


def _authed_client(user=None):
    c = Client()
    c.force_login(user or UserFactory())
    return c


# --- Test 1: tracer bullet ---


@pytest.mark.django_db
def test_pdf_view_returns_200_for_authenticated_user(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    assert response.status_code == http.HTTPStatus.OK


# --- Test 2b: signed token accepted ---


@pytest.mark.django_db
def test_pdf_view_allows_request_with_valid_signed_token(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    token = _signed_token(assessment.pk)
    response = Client().get(url, {"token": token}, REMOTE_ADDR="1.2.3.4")

    assert response.status_code == http.HTTPStatus.OK


# --- Test 3: auth required, no token or bad token ---


@pytest.mark.django_db
def test_pdf_view_returns_403_for_unauthenticated_request_without_token(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    response = Client().get(url, REMOTE_ADDR="1.2.3.4")

    assert response.status_code == http.HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_pdf_view_returns_403_for_invalid_signed_token(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    response = Client().get(url, {"token": "not-a-valid-token"}, REMOTE_ADDR="1.2.3.4")

    assert response.status_code == http.HTTPStatus.FORBIDDEN


# --- Test 4: toc_page_numbers in context ---


@pytest.mark.django_db
def test_pdf_view_context_has_toc_page_numbers(monkeypatch):
    assessment, _category = _make_assessment_with_category(category_name="Finance")
    assessment.name = "Q1 Review"
    assessment.save()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)

    toc = response.context["toc_page_numbers"]
    assert isinstance(toc, dict)
    assert toc["CBA Score"] == 3
    assert toc["Visualizations"] == 4
    assert toc["Analysis for Q1 Review"] == 5
    assert toc["analysis:Finance"] == 6
    assert toc["Recommendations"] == 7
    assert toc["12-Month Roadmap"] == 9


# --- Test 5: cover page content ---


@pytest.mark.django_db
def test_pdf_view_cover_page_contains_client_name_assessment_name_and_date(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    assessment.name = "Q1 Review"
    assessment.save()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert assessment.client.business_name in content
    assert "Q1 Review" in content
    assert "Complete Business Report" in content


# --- Test 6: ToC renders section names and page numbers ---


@pytest.mark.django_db
def test_pdf_view_toc_renders_section_names_and_page_numbers(monkeypatch):
    assessment, _ = _make_assessment_with_category(category_name="Finance")
    assessment.name = "Q1 Review"
    assessment.save()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "CBA Score" in content
    assert "Visualizations" in content
    assert "12-Month Roadmap" in content
    assert "Potential Challenges" in content
    # Page numbers from calculator (1 category: Finance)
    assert ">3<" in content  # CBA Score page
    assert ">4<" in content  # Visualizations page


# --- Test 7: Score overview per-category scores ---


@pytest.mark.django_db
def test_pdf_view_score_overview_renders_category_scores(monkeypatch):
    assessment, _category = _make_assessment_with_category(category_name="Finance")
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "Finance" in content
    assert "CBA Score" in content


# --- Test 8: Executive summary appears before category analysis sections ---


@pytest.mark.django_db
def test_pdf_view_executive_summary_appears_before_category_analysis(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    exec_pos = content.index("overall narrative")
    cat_pos = content.index("cat overview")
    assert exec_pos < cat_pos


# --- Test 9: Recommendations overview appears before per-category recs ---


@pytest.mark.django_db
def test_pdf_view_recommendations_overview_appears_before_category_recs(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    overview_pos = content.index("recommendations overview narrative")
    rec_pos = content.index("r1")
    assert overview_pos < rec_pos


# --- Test 10: All 12 roadmap months with Goals / Action Items / Challenges ---


@pytest.mark.django_db
def test_pdf_view_renders_all_12_roadmap_months(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    for n in range(1, 13):
        assert f"Month {n}" in content
    assert content.count("Goals") == 12
    assert content.count("Action Items") == 12
    assert content.count("Challenges") >= 12


# --- Test 11: Closing sections ---


@pytest.mark.django_db
def test_pdf_view_renders_closing_sections(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "Potential Challenges" in content
    assert "potential challenge 1" in content
    assert "Post-Implementation Outcomes" in content
    assert "outcome 1" in content
    assert "Closing Reflections" in content
    assert "reflection 1" in content


# --- Test 12: No navigation chrome ---


@pytest.mark.django_db
def test_pdf_view_has_no_navigation_or_feedback_form(monkeypatch):
    assessment, _ = _make_assessment_with_category()
    _make_report(assessment, monkeypatch)

    url = reverse("reports:pdf", kwargs={"pk": assessment.pk})
    content = _authed_client().get(url).content.decode()

    assert "breadcrumb" not in content
    assert "<form" not in content
    assert "{% extends" not in content
