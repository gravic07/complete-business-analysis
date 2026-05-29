from django.db import models

from complete_business_analysis_tool.core.models import BaseModel


class Feedback(BaseModel):
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    report_feedback = models.TextField(blank=True)


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
    potential_challenges = models.JSONField()
    post_implementation_outcomes = models.JSONField()
    closing_reflections = models.JSONField()


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
