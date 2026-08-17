import http
import json
import uuid

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


def _make_export(status=PDFExport.Status.PENDING, file=None):
    assessment = AssessmentFactory.create()
    return PDFExport.objects.create(assessment=assessment, status=status)


@pytest.mark.django_db
def test_status_endpoint_returns_complete_status_and_download_url(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    export = _make_export(status=PDFExport.Status.COMPLETE)
    fake_pdf = tmp_path / "pdf_exports" / "fake.pdf"
    fake_pdf.parent.mkdir(parents=True, exist_ok=True)
    fake_pdf.write_bytes(b"%PDF-1.4")
    export.file.name = "pdf_exports/fake.pdf"
    export.save(update_fields=["file"])

    url = reverse("reports:pdf_export_status", kwargs={"pk": export.pk})
    response = _authed_client().get(url)

    assert response.status_code == http.HTTPStatus.OK
    data = json.loads(response.content)
    assert data["status"] == PDFExport.Status.COMPLETE
    assert data["download_url"] != ""


@pytest.mark.django_db
def test_status_endpoint_returns_failed_status_with_no_download_url():
    export = _make_export(status=PDFExport.Status.FAILED)
    url = reverse("reports:pdf_export_status", kwargs={"pk": export.pk})

    response = _authed_client().get(url)

    assert response.status_code == http.HTTPStatus.OK
    data = json.loads(response.content)
    assert data["status"] == PDFExport.Status.FAILED
    assert data["download_url"] == ""


@pytest.mark.django_db
def test_status_endpoint_returns_pending_status_with_no_download_url():
    export = _make_export(status=PDFExport.Status.PENDING)
    url = reverse("reports:pdf_export_status", kwargs={"pk": export.pk})

    response = _authed_client().get(url)

    assert response.status_code == http.HTTPStatus.OK
    data = json.loads(response.content)
    assert data["status"] == PDFExport.Status.PENDING
    assert data["download_url"] == ""


@pytest.mark.django_db
def test_status_endpoint_returns_404_for_unknown_uuid():
    url = reverse("reports:pdf_export_status", kwargs={"pk": uuid.uuid4()})
    response = _authed_client().get(url)
    assert response.status_code == http.HTTPStatus.NOT_FOUND
