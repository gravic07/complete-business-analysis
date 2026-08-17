from unittest.mock import patch

import pytest
from django.test import TestCase

from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
)
from complete_business_analysis_tool.reports.models import PDFExport
from complete_business_analysis_tool.reports.tasks import generate_pdf_export


def _make_assessment():
    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(question=question)
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)
    return assessment


FAKE_PDF_BYTES = b"%PDF-1.4 fake pdf content"


class GeneratePdfExportTaskTest(TestCase):
    def _make_pdf_export(self, assessment=None):
        if assessment is None:
            assessment = _make_assessment()
        return PDFExport.objects.create(assessment=assessment)

    # --- Test 4: successful generation ---

    @patch(
        "complete_business_analysis_tool.reports.tasks.pdf_service.generate_pdf",
        return_value=FAKE_PDF_BYTES,
    )
    def test_successful_generation_sets_status_complete_and_saves_file(self, mock_gen):

        export = self._make_pdf_export()
        generate_pdf_export(str(export.pk))

        export.refresh_from_db()
        assert export.status == PDFExport.Status.COMPLETE
        assert export.file

    # --- Test 5: generation raises exception ---

    @patch(
        "complete_business_analysis_tool.reports.tasks.pdf_service.generate_pdf",
        side_effect=RuntimeError("browser crashed"),
    )
    def test_generation_exception_sets_status_failed_and_leaves_file_null(self, mock_gen):

        export = self._make_pdf_export()
        with pytest.raises(RuntimeError):
            generate_pdf_export(str(export.pk))

        export.refresh_from_db()
        assert export.status == PDFExport.Status.FAILED
        assert not export.file

    # --- Test 6: idempotency — already complete ---

    @patch("complete_business_analysis_tool.reports.tasks.pdf_service.generate_pdf")
    def test_already_complete_export_returns_early_without_generating(self, mock_gen):

        export = self._make_pdf_export()
        export.status = PDFExport.Status.COMPLETE
        export.save(update_fields=["status"])

        generate_pdf_export(str(export.pk))

        mock_gen.assert_not_called()

    # --- Test 7: idempotency — already failed ---

    @patch("complete_business_analysis_tool.reports.tasks.pdf_service.generate_pdf")
    def test_already_failed_export_returns_early_without_generating(self, mock_gen):

        export = self._make_pdf_export()
        export.status = PDFExport.Status.FAILED
        export.save(update_fields=["status"])

        generate_pdf_export(str(export.pk))

        mock_gen.assert_not_called()
