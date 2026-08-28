"""Pure business logic for the assessments app."""

from __future__ import annotations

from dataclasses import dataclass

from complete_business_analysis_tool.assessments.models import (
    Assessment,
    TemplateQuestion,
)


@dataclass(frozen=True)
class AssessmentCompletionStatus:
    """Whether an Assessment is eligible to be marked complete, and why not."""

    guidance_submitted: bool
    all_questions_answered: bool

    @property
    def eligible(self) -> bool:
        return self.guidance_submitted and self.all_questions_answered

    @property
    def reasons(self) -> list[str]:
        """Human-readable reasons this assessment isn't eligible yet."""
        reasons = []
        if not self.guidance_submitted:
            reasons.append("Category Guidance has not been submitted.")
        if not self.all_questions_answered:
            reasons.append("Not all questions have been answered.")
        return reasons


def assessment_completion_status(assessment: Assessment) -> AssessmentCompletionStatus:
    """Check whether assessment is eligible to be marked complete.

    Pure function: no HTTP concerns, callable from a view, task, or shell.
    """
    required_question_ids = set(
        TemplateQuestion.objects.filter(
            template_id=assessment.template_id,
        ).values_list("question_id", flat=True),
    )
    answered_question_ids = set(
        assessment.answers.values_list("question_id", flat=True),
    )

    return AssessmentCompletionStatus(
        guidance_submitted=assessment.guidance_submitted_at is not None,
        all_questions_answered=required_question_ids <= answered_question_ids,
    )
