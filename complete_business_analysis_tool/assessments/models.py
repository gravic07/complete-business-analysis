"""Django models for the assessments application."""

from django.db import models

from complete_business_analysis_tool.core.models import BaseModel


class Category(BaseModel):
    """Assessment category intended to group questions."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Question(BaseModel):
    """Reusable multiple-choice question to be attached to assessments."""

    body = models.TextField()
    category = models.ForeignKey(
        "Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions",
    )

    def __str__(self) -> str:
        return self.body[:80]


class QuestionOption(BaseModel):
    """A selectable choice for a multiple-choice question."""

    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=500)
    rank = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        ordering = ["rank"]
        unique_together = [["question", "rank"]]

    def __str__(self) -> str:
        return f"{self.question} — {self.text}"


class AssessmentTemplate(BaseModel):
    """Template defining which questions an assessment will ask."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.title


class TemplateQuestion(BaseModel):
    """Join table linking questions to an assessment template with ordering."""

    template = models.ForeignKey(
        "AssessmentTemplate",
        on_delete=models.CASCADE,
        related_name="template_questions",
    )
    question = models.ForeignKey(
        "Question",
        on_delete=models.PROTECT,
        related_name="template_questions",
    )
    order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [["template", "question"]]
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.template} — {self.question}"


class Assessment(BaseModel):
    """A completed or in-progress instance of an assessment template."""

    template = models.ForeignKey(
        "AssessmentTemplate",
        on_delete=models.PROTECT,
        related_name="assessments",
    )

    def __str__(self) -> str:
        return f"{self.template} ({self.created_at:%Y-%m-%d})"


class Answer(BaseModel):
    """A single answered question within an assessment.

    Snapshots preserve the question and option state at answer time so that
    historical answers remain accurate even if questions or options are later
    modified or deleted.
    """

    assessment = models.ForeignKey(
        "Assessment",
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "Question",
        on_delete=models.SET_NULL,
        null=True,
        related_name="answers",
    )
    selected_option = models.ForeignKey(
        "QuestionOption",
        on_delete=models.SET_NULL,
        null=True,
        related_name="answers",
    )
    question_snapshot = models.TextField()
    option_snapshot = models.JSONField()

    class Meta:
        unique_together = [["assessment", "question"]]

    def __str__(self) -> str:
        return f"{self.assessment} — {self.question_snapshot[:60]}"
