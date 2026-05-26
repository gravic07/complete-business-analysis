from django.db.models import Subquery

from complete_business_analysis_tool.reports.models import CategorySection


def latest_sections_by_category(assessment) -> list[CategorySection]:
    """Return the latest CategorySection per category across all Analysis runs."""
    return list(
        CategorySection.objects.filter(
            pk__in=Subquery(
                CategorySection.objects.filter(analysis__assessment=assessment)
                .order_by("category_id", "-analysis__created_at")
                .distinct("category_id")
                .values("pk"),
            ),
        )
        .select_related("category")
        .order_by("category__name"),
    )
