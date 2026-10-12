from http import HTTPStatus

import pytest
from django.core.files.base import ContentFile
from django.db.models import ProtectedError
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.factories import PDFExportFactory
from complete_business_analysis_tool.reports.models import PDFExport
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_pdf_export_status_choices_are_exactly_the_four_expected_values():
    choices = {value for value, _ in PDFExport.Status.choices}
    assert choices == {"pending", "processing", "complete", "failed"}


@pytest.mark.django_db
def test_deleting_user_who_triggered_a_pdf_export_is_refused():
    user = UserFactory.create()
    PDFExportFactory.create(created_by=user, assessment=AssessmentFactory.create())

    with pytest.raises(ProtectedError):
        user.delete()


@pytest.mark.django_db
def test_admin_pdf_export_changelist_shows_created_by(admin_client):
    PDFExportFactory.create()

    response = admin_client.get(reverse("admin:reports_pdfexport_changelist"))

    assert response.status_code == HTTPStatus.OK
    assert "column-created_by" in response.content.decode()


@pytest.mark.django_db
def test_admin_pdf_export_change_page_shows_file_name_without_media_link(
    admin_client,
    settings,
    tmp_path,
):
    settings.MEDIA_ROOT = str(tmp_path)
    export = PDFExportFactory.create(status=PDFExport.Status.COMPLETE)
    export.file.save("Acme_Report_20260101.pdf", ContentFile(b"%PDF-1.4"))

    response = admin_client.get(
        reverse("admin:reports_pdfexport_change", args=[export.pk]),
    )

    content = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "Acme_Report_20260101.pdf" in content
    assert export.file.url not in content
