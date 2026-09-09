"""Management command to run analysis and generate a report for an assessment."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.models import Assessment
from complete_business_analysis_tool.assessments.services import (
    assessment_completion_status,
)


class Command(BaseCommand):
    help = "Create an Analysis for an assessment and run report generation synchronously."

    def add_arguments(self, parser):
        parser.add_argument("assessment_id", help="UUID of the Assessment to analyse")

    def handle(self, *args, **options):
        assessment_id = options["assessment_id"]

        try:
            assessment = Assessment.objects.select_related("template", "client").get(
                id=assessment_id,
            )
        except Assessment.DoesNotExist as exc:
            msg = f"No Assessment found with id '{assessment_id}'"
            raise CommandError(msg) from exc

        self.stdout.write(
            f"Assessment:  {assessment.template.title} ({assessment.client})",
        )

        completion = assessment_completion_status(assessment)
        if not completion.all_questions_answered:
            msg = (
                f"Assessment '{assessment_id}' has unanswered questions; "
                "cannot run analysis."
            )
            raise CommandError(msg)

        update_fields: list[str] = []

        if not completion.guidance_submitted:
            assessment.guidance_submitted_at = timezone.now()
            update_fields.append("guidance_submitted_at")
            self.stdout.write(
                "Guidance:    none provided — treating as intentionally empty",
            )

        if assessment.status != Assessment.Status.COMPLETE:
            self.stdout.write(
                f"Status:      {assessment.status} → {Assessment.Status.COMPLETE}",
            )
            assessment.status = Assessment.Status.COMPLETE
            update_fields.append("status")

        if update_fields:
            assessment.save(update_fields=update_fields)

        analysis = Analysis.objects.create(assessment=assessment)
        self.stdout.write(f"Analysis:    {analysis.pk}  →  running...")

        run_analysis(str(analysis.pk))

        analysis.refresh_from_db()
        status_display = (
            self.style.SUCCESS(analysis.status)
            if analysis.status == "complete"
            else self.style.ERROR(analysis.status)
        )
        self.stdout.write(f"Status:      {status_display}")
        self.stdout.write(f"Report URL:  /reports/{assessment.pk}/")
