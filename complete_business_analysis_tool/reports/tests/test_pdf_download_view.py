"""Team-scoped PDF Report download (ADR 0013)."""

import http

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.reports.factories import PDFExportFactory
from complete_business_analysis_tool.reports.models import PDFExport
from complete_business_analysis_tool.users.tests.factories import UserFactory

PDF_BYTES = b"%PDF-1.4 fake"


@pytest.fixture(autouse=True)
def _media_root(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


def _logged_in_client(user):
    c = Client()
    c.force_login(user)
    return c


def _complete_export(**kwargs):
    export = PDFExportFactory.create(status=PDFExport.Status.COMPLETE, **kwargs)
    export.file.save("Acme_Initial_Report_20260101.pdf", ContentFile(PDF_BYTES))
    return export


def _download_url(export):
    return reverse("reports:pdf_download", kwargs={"pk": export.pk})


@pytest.mark.django_db
def test_owning_team_member_downloads_pdf_as_attachment_with_friendly_filename():
    export = _complete_export()
    teammate = UserFactory.create(team=export.created_by.team)

    response = _logged_in_client(teammate).get(_download_url(export))

    assert response.status_code == http.HTTPStatus.OK
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == (
        'attachment; filename="Acme_Initial_Report_20260101.pdf"'
    )
    assert b"".join(response.streaming_content) == PDF_BYTES


@pytest.mark.django_db
def test_other_team_member_gets_404():
    export = _complete_export()

    response = _logged_in_client(UserFactory.create()).get(_download_url(export))

    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_anonymous_request_redirects_to_login():
    export = _complete_export()
    url = _download_url(export)

    response = Client().get(url)

    assert response.status_code == http.HTTPStatus.FOUND
    assert response["Location"] == f"{reverse('account_login')}?next={url}"


@pytest.mark.django_db
def test_user_without_team_is_redirected_to_no_team_page():
    export = _complete_export()

    response = _logged_in_client(UserFactory.create(team=None)).get(
        _download_url(export),
    )

    assert response.status_code == http.HTTPStatus.FOUND
    assert response["Location"] == reverse("no_team")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        PDFExport.Status.PENDING,
        PDFExport.Status.PROCESSING,
        PDFExport.Status.FAILED,
    ],
)
def test_incomplete_export_returns_404(status):
    export = _complete_export()
    export.status = status
    export.save(update_fields=["status"])

    response = _logged_in_client(export.created_by).get(_download_url(export))

    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_complete_export_without_file_returns_404():
    export = PDFExportFactory.create(status=PDFExport.Status.COMPLETE)

    response = _logged_in_client(export.created_by).get(_download_url(export))

    assert response.status_code == http.HTTPStatus.NOT_FOUND
