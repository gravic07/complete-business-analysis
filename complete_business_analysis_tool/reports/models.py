from django.db import models

from complete_business_analysis_tool.core.models import BaseModel


class Feedback(BaseModel):
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    overall_text = models.TextField(blank=True)


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


class ReportSection(BaseModel):
    analysis = models.ForeignKey(
        "analysis.Analysis",
        on_delete=models.CASCADE,
        related_name="report_sections",
    )
    category = models.ForeignKey(
        "assessments.Category",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="report_sections",
    )
    content = models.TextField()

    class Meta(BaseModel.Meta):
        unique_together = [["analysis", "category"]]
