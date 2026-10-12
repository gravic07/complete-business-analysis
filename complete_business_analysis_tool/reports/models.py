from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from complete_business_analysis_tool.core.models import BaseModel

if TYPE_CHECKING:
    from complete_business_analysis_tool.teams.models import Team


class FeedbackQuerySet(models.QuerySet["Feedback"]):
    def for_team(self, team: Team | None) -> FeedbackQuerySet:
        """Feedback whose Assessment's Client is owned by ``team`` (ADR 0013)."""
        return self.filter(assessment__client__team=team)


class Feedback(BaseModel):
    objects = FeedbackQuerySet.as_manager()

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    report_feedback = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )


class CategoryFeedback(BaseModel):
    feedback = models.ForeignKey(
        "Feedback",
        on_delete=models.CASCADE,
        related_name="category_feedbacks",
    )
    category = models.ForeignKey(
        "assessments.Category",
        on_delete=models.PROTECT,
        related_name="category_feedbacks",
    )
    text = models.TextField()


class CategorySection(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="category_sections",
    )
    category = models.ForeignKey(
        "assessments.Category",
        on_delete=models.PROTECT,
        related_name="category_sections",
    )
    overview = models.TextField()
    impact = models.TextField()
    path_forward = models.TextField()

    class Meta(BaseModel.Meta):
        unique_together = [["analysis", "category"]]


class ExecutiveSummary(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="executive_summaries",
    )
    content = models.TextField()

    class Meta(BaseModel.Meta):
        unique_together = [["analysis"]]


class RecommendationsOverview(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="recommendations_overviews",
    )
    content = models.TextField()

    class Meta(BaseModel.Meta):
        unique_together = [["analysis"]]


class Roadmap(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="roadmaps",
        unique=True,
    )
    months = models.JSONField()
    potential_challenges = models.TextField()
    post_implementation_outcomes = models.TextField()
    closing_reflections = models.TextField()


class PDFExportQuerySet(models.QuerySet["PDFExport"]):
    def for_team(self, team: Team | None) -> PDFExportQuerySet:
        """PDFExports whose Assessment's Client is owned by ``team`` (ADR 0013).

        Advisor-side only: the background PDF task looks exports up by pk and
        stays Team-agnostic.
        """
        return self.filter(assessment__client__team=team)


class PDFExport(BaseModel):
    objects = PDFExportQuerySet.as_manager()

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="pdf_exports",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    file = models.FileField(upload_to="pdf_exports/", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )


class CategoryRecommendations(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="category_recommendations",
    )
    category = models.ForeignKey(
        "assessments.Category",
        on_delete=models.PROTECT,
        related_name="category_recommendations",
    )
    recommendations = models.JSONField()

    class Meta(BaseModel.Meta):
        unique_together = [["analysis", "category"]]
