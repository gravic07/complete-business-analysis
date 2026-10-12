from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models

from complete_business_analysis_tool.core.models import BaseModel

if TYPE_CHECKING:
    from complete_business_analysis_tool.teams.models import Team


class AnalysisQuerySet(models.QuerySet["Analysis"]):
    def for_team(self, team: Team | None) -> AnalysisQuerySet:
        """Analysis runs whose Assessment's Client is owned by ``team`` (ADR 0013)."""
        return self.filter(assessment__client__team=team)


class Analysis(BaseModel):
    objects = AnalysisQuerySet.as_manager()

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    feedback = models.ForeignKey(
        "reports.Feedback",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyses",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_score = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )

    _ACTIVE_STATUSES = {Status.PENDING, Status.PROCESSING}

    def clean(self):
        super().clean()
        active = Analysis.objects.filter(
            assessment=self.assessment_id,
            status__in=self._ACTIVE_STATUSES,
        ).exclude(pk=self.pk)
        if active.exists():
            msg = "An Analysis is already pending or processing for this Assessment."
            raise ValidationError(msg)

    def __str__(self) -> str:
        return f"Analysis({self.assessment}, {self.status})"


class CategoryScore(BaseModel):
    analysis = models.ForeignKey(
        "Analysis",
        on_delete=models.CASCADE,
        related_name="category_scores",
    )
    category = models.ForeignKey(
        "assessments.Category",
        on_delete=models.PROTECT,
        related_name="category_scores",
    )
    score = models.DecimalField(max_digits=10, decimal_places=4)
    max_possible_score = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta(BaseModel.Meta):
        unique_together = [["analysis", "category"]]

    def __str__(self) -> str:
        return f"CategoryScore({self.category}, {self.score})"
