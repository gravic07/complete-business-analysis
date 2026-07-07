import logging
import re

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.signing import TimestampSigner
from django.utils import timezone

from complete_business_analysis_tool.reports import pdf_service
from complete_business_analysis_tool.reports.models import PDFExport

logger = logging.getLogger(__name__)


def _safe_name(text: str) -> str:
    return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")


@shared_task()
def generate_pdf_export(pdf_export_id: str) -> None:
    export = PDFExport.objects.select_related("assessment__client").get(pk=pdf_export_id)

    if export.status in (PDFExport.Status.COMPLETE, PDFExport.Status.FAILED):
        return

    export.status = PDFExport.Status.PROCESSING
    export.save(update_fields=["status"])

    assessment_pk = str(export.assessment_id)
    token = TimestampSigner().sign(assessment_pk)

    try:
        pdf_bytes = pdf_service.generate_pdf(
            assessment_pk,
            token,
            header_left=export.assessment.name.upper(),
            header_right=export.assessment.client.business_name.upper(),
        )
        company = _safe_name(export.assessment.client.business_name)
        title = _safe_name(export.assessment.name)
        date_str = timezone.now().date().strftime("%Y%m%d")
        filename = f"{company}_{title}_{date_str}.pdf"
        export.file.save(filename, ContentFile(pdf_bytes), save=True)
    except Exception:
        logger.exception("PDF export %s failed", pdf_export_id)
        export.status = PDFExport.Status.FAILED
        export.save(update_fields=["status"])
        raise

    export.status = PDFExport.Status.COMPLETE
    export.save(update_fields=["status"])


@shared_task()
def fail_stale_pdf_exports() -> int:
    """Recover PDFExport rows orphaned by a killed or crashed worker.

    Same failure mode as analysis.tasks.fail_stale_analyses: a SIGKILLed
    worker never runs the except block that would set status to FAILED.
    """
    cutoff = timezone.now() - settings.STALE_PROCESSING_THRESHOLD
    stale = PDFExport.objects.filter(
        status=PDFExport.Status.PROCESSING,
        updated_at__lt=cutoff,
    )
    stale_ids = list(stale.values_list("pk", flat=True))
    if stale_ids:
        logger.warning("Marking stale processing PDF exports as failed: %s", stale_ids)
        stale.update(status=PDFExport.Status.FAILED)
    return len(stale_ids)
