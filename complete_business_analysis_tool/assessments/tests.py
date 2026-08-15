import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    QuestionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.services import (
    assessment_completion_status,
)
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_assessment_name_defaults_to_initial_report():
    assessment = AssessmentFactory()
    assert assessment.name == "Initial Report"


@pytest.mark.django_db
def test_assessment_detail_lists_all_analysis_runs_with_status_and_timestamp():
    assessment = AssessmentFactory()
    analysis1 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.COMPLETE,
    )
    _analysis2 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.FAILED,
    )

    user = UserFactory()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert str(analysis1.pk) in content or "Complete" in content
    assert "Complete" in content
    assert "Failed" in content


@pytest.mark.django_db
def test_completion_status_ineligible_when_guidance_not_submitted_even_if_answered():
    assessment = AssessmentFactory(guidance_submitted_at=None)
    question = QuestionFactory()
    TemplateQuestionFactory(template=assessment.template, question=question)
    AnswerFactory(assessment=assessment, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is False
    assert status.all_questions_answered is True


@pytest.mark.django_db
def test_completion_status_ineligible_when_unanswered_despite_guidance_submitted():
    assessment = AssessmentFactory(guidance_submitted_at=timezone.now())
    question = QuestionFactory()
    TemplateQuestionFactory(template=assessment.template, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is True
    assert status.all_questions_answered is False


@pytest.mark.django_db
def test_completion_status_ineligible_with_both_reasons_when_neither_condition_met():
    assessment = AssessmentFactory(guidance_submitted_at=None)
    question = QuestionFactory()
    TemplateQuestionFactory(template=assessment.template, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is False
    assert status.all_questions_answered is False


@pytest.mark.django_db
def test_completion_status_eligible_when_guidance_submitted_and_all_questions_answered():
    assessment = AssessmentFactory(guidance_submitted_at=timezone.now())
    question = QuestionFactory()
    TemplateQuestionFactory(template=assessment.template, question=question)
    AnswerFactory(assessment=assessment, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is True
    assert status.guidance_submitted is True
    assert status.all_questions_answered is True
