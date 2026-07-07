from __future__ import annotations

from complete_business_analysis_tool.reports.models import (
    CategoryRecommendations,
    CategorySection,
    ExecutiveSummary,
    RecommendationsOverview,
    Roadmap,
)

from .models import Analysis, CategoryScore
from .tasks import run_analysis


def start_analysis(assessment, feedback=None) -> Analysis:
    """Create an Analysis for assessment and dispatch run_analysis via Celery.

    Raises django.core.exceptions.ValidationError if an Analysis is already
    pending or processing for this assessment (enforced by Analysis.clean()).
    """
    analysis = Analysis(assessment=assessment, feedback=feedback)
    analysis.full_clean()
    analysis.save()
    run_analysis.delay(str(analysis.pk))
    return analysis


def analysis_progress_message(analysis: Analysis) -> str:  # noqa: PLR0911
    """Best-effort human-readable status for an in-flight Analysis.

    Derived purely from which content rows already exist for this analysis,
    since _run_analysis_work (analysis/tasks.py) always runs its steps in the
    same fixed order: scores -> sections -> recommendations -> overview ->
    executive summary -> roadmap.
    """
    total = CategoryScore.objects.filter(analysis=analysis).count()
    if Roadmap.objects.filter(analysis=analysis).exists():
        return "Finalizing your report…"
    if ExecutiveSummary.objects.filter(analysis=analysis).exists():
        return "Building your 12-month roadmap…"
    if RecommendationsOverview.objects.filter(analysis=analysis).exists():
        return "Writing your executive summary…"
    recs_done = CategoryRecommendations.objects.filter(analysis=analysis).count()
    if total and recs_done >= total:
        return "Drafting your recommendations overview…"
    if recs_done:
        return f"Generating recommendations ({recs_done}/{total})…"
    sections_done = CategorySection.objects.filter(analysis=analysis).count()
    if total and sections_done >= total:
        return "Generating recommendations for each category…"
    if sections_done:
        return f"Analyzing category performance ({sections_done}/{total})…"
    if total:
        return "Analyzing category performance…"
    return "Scoring your responses…"
