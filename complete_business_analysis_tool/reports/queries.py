from django.db.models import Subquery

from complete_business_analysis_tool.reports.models import ReportSection


def latest_sections_by_category(assessment) -> list[ReportSection]:
    """Return the latest ReportSection per category across all Analysis runs.

    Overall section (category=None) is first, then categories ordered by name.
    """
    sections = list(
        ReportSection.objects.filter(
            pk__in=Subquery(
                ReportSection.objects.filter(analysis__assessment=assessment)
                .order_by("category_id", "-analysis__created_at")
                .distinct("category_id")
                .values("pk"),
            ),
        )
        .select_related("category")
        .order_by("category__name"),
    )
    overall = [s for s in sections if s.category is None]
    categorized = [s for s in sections if s.category is not None]
    return overall + categorized
