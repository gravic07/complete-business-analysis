import pytest

from complete_business_analysis_tool.reports.models import PDFExport


@pytest.mark.django_db
def test_pdf_export_status_choices_are_exactly_the_four_expected_values():
    choices = {value for value, _ in PDFExport.Status.choices}
    assert choices == {"pending", "processing", "complete", "failed"}
