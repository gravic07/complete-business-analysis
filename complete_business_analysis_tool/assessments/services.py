"""Pure business logic for the assessments app."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from django.db import transaction

from complete_business_analysis_tool.assessments.models import (
    Assessment,
    ClientAccessLink,
    TemplateQuestion,
)


def issue_client_access_token() -> str:
    """Generate a fresh opaque token for a ClientAccessLink."""
    return secrets.token_urlsafe(32)


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


def generate_client_access_link(
    assessment: Assessment,
    link_type: str,
) -> ClientAccessLink:
    """Get or create the active link for (assessment, link_type).

    Issues a fresh token only when no row exists yet, or the existing row is
    revoked. An already-active row is returned unchanged.
    """
    with transaction.atomic():
        link, created = ClientAccessLink.objects.select_for_update().get_or_create(
            assessment=assessment,
            link_type=link_type,
            defaults={"token": issue_client_access_token},
        )
        if not created and link.status == ClientAccessLink.Status.REVOKED:
            link = regenerate_client_access_link(link)
    return link


def revoke_client_access_link(link: ClientAccessLink) -> ClientAccessLink:
    """Mark a link revoked without issuing a replacement token."""
    link.status = ClientAccessLink.Status.REVOKED
    link.save(update_fields=["status", "updated_at"])
    return link


def regenerate_client_access_link(link: ClientAccessLink) -> ClientAccessLink:
    """Overwrite a link's token in place, ensuring it is left active."""
    link.token = issue_client_access_token()
    link.status = ClientAccessLink.Status.ACTIVE
    link.save(update_fields=["token", "status", "updated_at"])
    return link


def is_client_access_link_valid(token: str) -> bool:
    """Report whether a token resolves to a link that currently grants access."""
    try:
        link = ClientAccessLink.objects.select_related("assessment").get(token=token)
    except ClientAccessLink.DoesNotExist:
        return False
    if link.status == ClientAccessLink.Status.REVOKED:
        return False
    return link.assessment.status != Assessment.Status.COMPLETE
