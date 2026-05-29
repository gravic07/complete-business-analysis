from django.db.models import Subquery

from complete_business_analysis_tool.reports.models import (
    CategoryRecommendations,
    CategorySection,
    ExecutiveSummary,
    RecommendationsOverview,
    Roadmap,
)


def latest_category_sections(assessment) -> list[CategorySection]:
    """
    Return the latest CategorySection per category across all Analysis runs,
    ordered by name.
    """
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


def latest_category_recommendations(assessment) -> list[CategoryRecommendations]:
    """
    Return the latest CategoryRecommendations per category across all Analysis runs,
    ordered by category name.
    """
    return list(
        CategoryRecommendations.objects.filter(
            pk__in=Subquery(
                CategoryRecommendations.objects.filter(
                    analysis__assessment=assessment,
                )
                .order_by("category_id", "-analysis__created_at")
                .distinct("category_id")
                .values("pk"),
            ),
        )
        .select_related("category")
        .order_by("category__name"),
    )


def latest_executive_summary(assessment) -> ExecutiveSummary | None:
    """Return the latest ExecutiveSummary across all Analysis runs, or None."""
    return (
        ExecutiveSummary.objects.filter(analysis__assessment=assessment)
        .order_by("-analysis__created_at")
        .first()
    )


def latest_recommendations_overview(assessment) -> RecommendationsOverview | None:
    """Return the latest RecommendationsOverview across all Analysis runs, or None."""
    return (
        RecommendationsOverview.objects.filter(analysis__assessment=assessment)
        .order_by("-analysis__created_at")
        .first()
    )


def latest_roadmap(assessment) -> Roadmap | None:
    """Return the latest Roadmap across all Analysis runs, or None."""
    return (
        Roadmap.objects.filter(analysis__assessment=assessment)
        .order_by("-analysis__created_at")
        .first()
    )
