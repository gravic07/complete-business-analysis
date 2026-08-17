import http
import json
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import PDFExport
from complete_business_analysis_tool.users.tests.factories import UserFactory


def _authed_client(user=None):
    c = Client()
    c.force_login(user or UserFactory.create())
    return c


@pytest.mark.django_db
def test_trigger_pdf_export_creates_pending_export_and_returns_id():
    assessment = AssessmentFactory.create()
    url = reverse("reports:export_pdf", kwargs={"pk": assessment.pk})

    with patch(
        "complete_business_analysis_tool.reports.views.generate_pdf_export",
    ) as mock_task:
        mock_task.delay.return_value = None
        response = _authed_client().post(url)

    assert response.status_code == http.HTTPStatus.OK
    data = json.loads(response.content)
    assert "pdf_export_id" in data

    export = PDFExport.objects.get(pk=data["pdf_export_id"])
    assert export.assessment == assessment
    assert export.status == PDFExport.Status.PENDING


@pytest.mark.django_db
def test_trigger_pdf_export_calls_celery_task_with_export_id():
    assessment = AssessmentFactory.create()
    url = reverse("reports:export_pdf", kwargs={"pk": assessment.pk})

    with patch(
        "complete_business_analysis_tool.reports.views.generate_pdf_export",
    ) as mock_task:
        mock_task.delay.return_value = None
        _authed_client().post(url)

    mock_task.delay.assert_called_once()
    called_id = mock_task.delay.call_args[0][0]
    assert PDFExport.objects.filter(pk=called_id).exists()


@pytest.mark.django_db
def test_trigger_pdf_export_returns_405_for_non_post():
    assessment = AssessmentFactory.create()
    url = reverse("reports:export_pdf", kwargs={"pk": assessment.pk})
    response = _authed_client().get(url)
    assert response.status_code == http.HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_trigger_pdf_export_redirects_unauthenticated():
    assessment = AssessmentFactory.create()
    url = reverse("reports:export_pdf", kwargs={"pk": assessment.pk})
    response = Client().post(url)
    assert response.status_code == http.HTTPStatus.FOUND
    assert "/accounts/" in response["Location"]
