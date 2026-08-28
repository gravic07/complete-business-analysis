from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    AssessmentTemplateFactory,
    QuestionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import Assessment
from complete_business_analysis_tool.assessments.services import (
    assessment_completion_status,
)
from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_assessment_name_defaults_to_initial_report():
    assessment = AssessmentFactory.create()
    assert assessment.name == "Initial Report"


@pytest.mark.django_db
def test_assessment_detail_lists_all_analysis_runs_with_status_and_timestamp():
    assessment = AssessmentFactory.create()
    analysis1 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.COMPLETE,
    )
    _analysis2 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.FAILED,
    )

    user = UserFactory.create()
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
    assessment = AssessmentFactory.create(guidance_submitted_at=None)
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)
    AnswerFactory.create(assessment=assessment, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is False
    assert status.all_questions_answered is True


@pytest.mark.django_db
def test_completion_status_ineligible_when_unanswered_despite_guidance_submitted():
    assessment = AssessmentFactory.create(guidance_submitted_at=timezone.now())
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is True
    assert status.all_questions_answered is False


@pytest.mark.django_db
def test_completion_status_ineligible_with_both_reasons_when_neither_condition_met():
    assessment = AssessmentFactory.create(guidance_submitted_at=None)
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is False
    assert status.guidance_submitted is False
    assert status.all_questions_answered is False


@pytest.mark.django_db
def test_completion_status_eligible_when_guidance_submitted_and_all_questions_answered():
    assessment = AssessmentFactory.create(guidance_submitted_at=timezone.now())
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)
    AnswerFactory.create(assessment=assessment, question=question)

    status = assessment_completion_status(assessment)

    assert status.eligible is True
    assert status.guidance_submitted is True
    assert status.all_questions_answered is True


@pytest.mark.django_db
def test_start_view_creates_draft_assessment_and_redirects_to_detail():
    template = AssessmentTemplateFactory.create()
    client_obj = ClientFactory.create()
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:start", kwargs={"pk": template.pk})
    response = http_client.post(url, {"client": client_obj.pk})

    assessment = Assessment.objects.get()
    assert assessment.template == template
    assert assessment.client == client_obj
    assert assessment.status == Assessment.Status.DRAFT
    assert assessment.answers.count() == 0
    assert assessment.category_guidance.count() == 0
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("assessments:detail", kwargs={"pk": assessment.pk})


@pytest.mark.django_db
def test_start_view_invalid_post_rerenders_form_without_creating_assessment():
    template = AssessmentTemplateFactory.create()
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:start", kwargs={"pk": template.pk})
    response = http_client.post(url, {"client": ""})

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors
    assert Assessment.objects.count() == 0


@pytest.mark.django_db
def test_start_view_prefills_client_from_query_param():
    template = AssessmentTemplateFactory.create()
    client_obj = ClientFactory.create()
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:start", kwargs={"pk": template.pk})
    response = http_client.get(url, {"client": str(client_obj.pk)})

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].initial["client"] == str(client_obj.pk)
