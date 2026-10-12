"""Team scoping for Reports, Analysis runs, Feedback and PDFExports (ADR 0013).

Every test sets up two Teams: ``ours`` (the requesting User's) and ``theirs``.
"""

import http
import json
from unittest.mock import patch
from urllib.parse import urlsplit

import pytest
from django.core.signing import TimestampSigner
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports import pdf_service
from complete_business_analysis_tool.reports.factories import (
    FeedbackFactory,
    PDFExportFactory,
)
from complete_business_analysis_tool.reports.models import Feedback, PDFExport
from complete_business_analysis_tool.reports.tasks import generate_pdf_export


@pytest.fixture
def ours(user):
    """An Assessment owned by the requesting User's Team."""
    return AssessmentFactory.create(created_by=user, name="Our Report")


@pytest.fixture
def theirs(db):
    """An Assessment owned by another Team."""
    return AssessmentFactory.create(name="Their Report")


@pytest.fixture
def http_client(user):
    c = Client()
    c.force_login(user)
    return c


# --- for_team() querysets ---


@pytest.mark.django_db
def test_analysis_for_team_returns_only_that_teams_analyses(user, ours, theirs):
    own = Analysis.objects.create(assessment=ours)
    Analysis.objects.create(assessment=theirs)

    assert list(Analysis.objects.for_team(user.team)) == [own]


@pytest.mark.django_db
def test_feedback_for_team_returns_only_that_teams_feedback(user, ours, theirs):
    own = FeedbackFactory.create(assessment=ours)
    FeedbackFactory.create(assessment=theirs)

    assert list(Feedback.objects.for_team(user.team)) == [own]


@pytest.mark.django_db
def test_pdf_export_for_team_returns_only_that_teams_exports(user, ours, theirs):
    own = PDFExportFactory.create(assessment=ours)
    PDFExportFactory.create(assessment=theirs)

    assert list(PDFExport.objects.for_team(user.team)) == [own]


# --- Assessment-keyed views ---


@pytest.mark.django_db
def test_report_page_404s_for_another_teams_assessment(http_client, ours, theirs):
    own = http_client.get(reverse("reports:report", kwargs={"pk": ours.pk}))
    other = http_client.get(reverse("reports:report", kwargs={"pk": theirs.pk}))

    assert own.status_code == http.HTTPStatus.OK
    assert other.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_submit_feedback_404s_for_another_teams_assessment(http_client, theirs):
    url = reverse("reports:submit_feedback", kwargs={"pk": theirs.pk})

    response = http_client.post(url, {"report_feedback": "Sneaky."})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert not Feedback.objects.exists()


@pytest.mark.django_db
def test_update_assessment_name_404s_for_another_teams_assessment(http_client, theirs):
    url = reverse("reports:rename", kwargs={"pk": theirs.pk})

    response = http_client.post(url, {"name": "Renamed"})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    theirs.refresh_from_db()
    assert theirs.name == "Their Report"


@pytest.mark.django_db
def test_trigger_analysis_404s_for_another_teams_assessment(http_client, theirs):
    url = reverse("reports:generate_analysis", kwargs={"pk": theirs.pk})

    with patch("complete_business_analysis_tool.analysis.services.run_analysis"):
        response = http_client.post(url)

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert not Analysis.objects.exists()


@pytest.mark.django_db
def test_trigger_analysis_rejects_another_teams_feedback(http_client, ours, theirs):
    their_feedback = FeedbackFactory.create(assessment=theirs)
    url = reverse("reports:generate_analysis", kwargs={"pk": ours.pk})

    with patch("complete_business_analysis_tool.analysis.services.run_analysis"):
        response = http_client.post(url, {"feedback_id": str(their_feedback.pk)})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert not Analysis.objects.exists()


@pytest.mark.django_db
def test_trigger_analysis_retry_rejects_another_teams_analysis(http_client, ours, theirs):
    their_analysis = Analysis.objects.create(
        assessment=theirs,
        status=Analysis.Status.FAILED,
    )
    url = reverse("reports:generate_analysis", kwargs={"pk": ours.pk})

    with patch("complete_business_analysis_tool.reports.views.run_analysis") as task:
        response = http_client.post(
            url,
            {"retry_analysis_id": str(their_analysis.pk)},
        )

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    task.delay.assert_not_called()
    their_analysis.refresh_from_db()
    assert their_analysis.status == Analysis.Status.FAILED


@pytest.mark.django_db
def test_trigger_pdf_export_404s_for_another_teams_assessment(http_client, theirs):
    url = reverse("reports:export_pdf", kwargs={"pk": theirs.pk})

    with patch(
        "complete_business_analysis_tool.reports.views.generate_pdf_export",
    ) as task:
        response = http_client.post(url)

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    task.delay.assert_not_called()
    assert not PDFExport.objects.exists()


# --- Status endpoints ---


@pytest.mark.django_db
def test_analysis_status_404s_for_another_teams_analysis(http_client, ours, theirs):
    own = Analysis.objects.create(assessment=ours)
    other = Analysis.objects.create(assessment=theirs)

    own_response = http_client.get(
        reverse("reports:analysis_status", kwargs={"pk": own.pk}),
    )
    other_response = http_client.get(
        reverse("reports:analysis_status", kwargs={"pk": other.pk}),
    )

    assert own_response.status_code == http.HTTPStatus.OK
    assert other_response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_pdf_export_status_404s_for_another_teams_export(http_client, ours, theirs):
    own = PDFExportFactory.create(assessment=ours)
    other = PDFExportFactory.create(assessment=theirs)

    own_response = http_client.get(
        reverse("reports:pdf_export_status", kwargs={"pk": own.pk}),
    )
    other_response = http_client.get(
        reverse("reports:pdf_export_status", kwargs={"pk": other.pk}),
    )

    assert own_response.status_code == http.HTTPStatus.OK
    assert other_response.status_code == http.HTTPStatus.NOT_FOUND


# --- PDF template page ---


@pytest.mark.django_db
def test_pdf_template_renders_for_owning_team(http_client, ours):
    response = http_client.get(reverse("reports:pdf", kwargs={"pk": ours.pk}))

    assert response.status_code == http.HTTPStatus.OK


@pytest.mark.django_db
def test_pdf_template_404s_for_logged_in_user_from_another_team(http_client, theirs):
    response = http_client.get(reverse("reports:pdf", kwargs={"pk": theirs.pk}))

    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_pdf_template_token_does_not_bypass_team_scope_when_logged_in(
    http_client,
    theirs,
):
    token = TimestampSigner().sign(str(theirs.pk))

    response = http_client.get(
        reverse("reports:pdf", kwargs={"pk": theirs.pk}),
        {"token": token},
    )

    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_pdf_template_signed_token_path_stays_team_agnostic(ours, theirs):
    for assessment in (ours, theirs):
        token = TimestampSigner().sign(str(assessment.pk))

        response = Client().get(
            reverse("reports:pdf", kwargs={"pk": assessment.pk}),
            {"token": token},
        )

        assert response.status_code == http.HTTPStatus.OK


# --- Home page ---


@pytest.mark.django_db
def test_home_analysis_count_reflects_only_requesting_users_team(
    http_client,
    ours,
    theirs,
):
    Analysis.objects.create(assessment=ours, status=Analysis.Status.COMPLETE)
    Analysis.objects.create(assessment=theirs, status=Analysis.Status.COMPLETE)
    Analysis.objects.create(assessment=theirs, status=Analysis.Status.COMPLETE)

    response = http_client.get(reverse("home"))

    assert response.context["analysis_count"] == 1


# --- End to end ---


@pytest.mark.django_db
def test_pdf_export_generates_end_to_end_for_owning_team(http_client, ours, theirs):
    """Trigger → background task → signed-token render hop → status, for our Team.

    Playwright is replaced by an anonymous test-client fetch of the same
    signed-token URL the task hands it, so the render hop is still exercised.
    """

    def fake_generate_pdf(assessment_pk, token, **kwargs):
        url = urlsplit(pdf_service._build_url(assessment_pk, token))  # noqa: SLF001
        rendered = Client().get(f"{url.path}?{url.query}")
        assert rendered.status_code == http.HTTPStatus.OK
        return b"%PDF-1.4 rendered"

    with patch(
        "complete_business_analysis_tool.reports.views.generate_pdf_export",
    ) as task:
        trigger = http_client.post(reverse("reports:export_pdf", kwargs={"pk": ours.pk}))
    export_id = json.loads(trigger.content)["pdf_export_id"]
    task.delay.assert_called_once_with(export_id)

    with patch(
        "complete_business_analysis_tool.reports.tasks.pdf_service.generate_pdf",
        side_effect=fake_generate_pdf,
    ):
        generate_pdf_export(export_id)

    status = http_client.get(
        reverse("reports:pdf_export_status", kwargs={"pk": export_id}),
    )
    data = json.loads(status.content)
    assert status.status_code == http.HTTPStatus.OK
    assert data["status"] == PDFExport.Status.COMPLETE
    assert data["download_url"] != ""
