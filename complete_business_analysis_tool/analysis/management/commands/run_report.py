"""Management command to run analysis and generate a report for an assessment."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.models import Assessment


class Command(BaseCommand):
    help = (
        "Create an Analysis for an assessment and run report generation synchronously."
    )

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
