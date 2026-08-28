import uuid
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    AssessmentTemplateFactory,
    CategoryFactory,
    CategoryGuidanceFactory,
    QuestionFactory,
    QuestionOptionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import (
    Assessment,
    CategoryGuidance,
)
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


@pytest.mark.django_db
def test_guidance_view_lists_template_categories_alphabetically_with_no_answers():
    template = AssessmentTemplateFactory.create()
    category_b = CategoryFactory.create(name="Bravo")
    category_a = CategoryFactory.create(name="Alpha")
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category_b),
    )
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category_a),
    )
    assessment = AssessmentFactory.create(template=template)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = http_client.get(url)

    categories = [c for c, _ in response.context["form"].get_category_fields()]
    assert categories == [category_a, category_b]
    assert assessment.answers.count() == 0


@pytest.mark.django_db
def test_guidance_view_requires_login():
    assessment = AssessmentFactory.create()

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = Client().get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url


@pytest.mark.django_db
def test_guidance_view_requires_login_even_when_assessment_is_complete():
    assessment = AssessmentFactory.create(status=Assessment.Status.COMPLETE)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = Client().get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url
    assert response.url != reverse("assessments:detail", kwargs={"pk": assessment.pk})


@pytest.mark.django_db
def test_guidance_view_all_blank_submit_succeeds_and_stamps_submitted_at():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
        guidance_submitted_at=None,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = http_client.post(url, {f"category_{category.pk.hex}": ""})

    assessment.refresh_from_db()
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("assessments:detail", kwargs={"pk": assessment.pk})
    assert assessment.guidance_submitted_at is not None
    assert assessment.category_guidance.count() == 0


@pytest.mark.django_db
def test_guidance_view_creates_rows_only_for_non_blank_fields():
    template = AssessmentTemplateFactory.create()
    category_with_text = CategoryFactory.create()
    category_blank = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category_with_text),
    )
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category_blank),
    )
    assessment = AssessmentFactory.create(template=template)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(
        url,
        {
            f"category_{category_with_text.pk.hex}": "Focus on cashflow.",
            f"category_{category_blank.pk.hex}": "",
        },
    )

    guidance_rows = CategoryGuidance.objects.filter(assessment=assessment)
    assert guidance_rows.count() == 1
    row = guidance_rows.get()
    assert row.category == category_with_text
    assert row.text == "Focus on cashflow."


@pytest.mark.django_db
def test_guidance_view_resubmit_updates_existing_row_not_duplicate():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(template=template)
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category,
        text="Original text.",
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"category_{category.pk.hex}": "Revised text."})

    guidance_rows = CategoryGuidance.objects.filter(assessment=assessment)
    assert guidance_rows.count() == 1
    assert guidance_rows.get().text == "Revised text."


@pytest.mark.django_db
def test_guidance_view_clearing_field_deletes_existing_row():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(template=template)
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category,
        text="Existing text.",
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"category_{category.pk.hex}": ""})

    assert not CategoryGuidance.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_guidance_view_advances_draft_assessment_to_in_progress():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"category_{category.pk.hex}": "Some notes."})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.IN_PROGRESS


@pytest.mark.django_db
def test_guidance_view_leaves_in_progress_assessment_in_progress():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.IN_PROGRESS,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"category_{category.pk.hex}": "Some notes."})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.IN_PROGRESS


@pytest.mark.django_db
def test_guidance_view_complete_assessment_rejects_get_with_message_no_404():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.COMPLETE,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = http_client.get(url, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain
    messages = [str(m) for m in response.context["messages"]]
    assert any("complete" in m.lower() for m in messages)


@pytest.mark.django_db
def test_guidance_view_complete_assessment_rejects_post_and_persists_nothing():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.COMPLETE,
        guidance_submitted_at=timezone.now(),
    )
    original_submitted_at = assessment.guidance_submitted_at
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"category_{category.pk.hex}": "New notes."})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    assert assessment.guidance_submitted_at == original_submitted_at
    assert not CategoryGuidance.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_guidance_view_prefills_fields_with_previously_entered_text():
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    TemplateQuestionFactory.create(
        template=template,
        question=QuestionFactory.create(category=category),
    )
    assessment = AssessmentFactory.create(template=template)
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category,
        text="Previously entered guidance.",
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = http_client.get(url)

    initial = response.context["form"].initial
    assert initial[f"category_{category.pk.hex}"] == "Previously entered guidance."


@pytest.mark.django_db
def test_answer_view_renders_one_field_per_question_grouped_by_category():
    template = AssessmentTemplateFactory.create()
    category_b = CategoryFactory.create(name="Bravo")
    category_a = CategoryFactory.create(name="Alpha")
    question_b = QuestionFactory.create(category=category_b)
    question_a = QuestionFactory.create(category=category_a)
    QuestionOptionFactory.create(question=question_b, rank=1)
    QuestionOptionFactory.create(question=question_a, rank=1)
    TemplateQuestionFactory.create(template=template, question=question_b, order=1)
    TemplateQuestionFactory.create(template=template, question=question_a, order=2)
    assessment = AssessmentFactory.create(template=template)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.get(url)

    grouped = response.context["form"].get_grouped_fields()
    assert [name for name, _ in grouped] == ["Bravo", "Alpha"]
    assert [len(fields) for _, fields in grouped] == [1, 1]


@pytest.mark.django_db
def test_answer_view_full_submit_creates_answers_against_existing_assessment():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(
        question=question,
        rank=2,
        text="Strong",
        weight=Decimal("2.0000"),
    )
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.post(url, {f"question_{question.pk.hex}": str(option.pk)})

    assert response.status_code == HTTPStatus.FOUND
    assert Assessment.objects.count() == 1
    answer = assessment.answers.get()
    assert answer.question == question
    assert answer.selected_option == option
    assert answer.question_snapshot == question.body
    assert answer.option_snapshot == {
        "id": str(option.pk),
        "text": option.text,
        "rank": option.rank,
        "weight": str(option.weight),
    }


@pytest.mark.django_db
def test_answer_view_partial_submit_fails_validation_no_answers_created():
    template = AssessmentTemplateFactory.create()
    question1 = QuestionFactory.create()
    question2 = QuestionFactory.create()
    option1 = QuestionOptionFactory.create(question=question1, rank=1)
    QuestionOptionFactory.create(question=question2, rank=1)
    TemplateQuestionFactory.create(template=template, question=question1)
    TemplateQuestionFactory.create(template=template, question=question2)
    assessment = AssessmentFactory.create(template=template)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.post(url, {f"question_{question1.pk.hex}": str(option1.pk)})

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors
    assert assessment.answers.count() == 0


@pytest.mark.django_db
def test_answer_view_resubmit_updates_existing_answer_not_duplicate():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option_low = QuestionOptionFactory.create(question=question, rank=1, text="Weak")
    option_high = QuestionOptionFactory.create(question=question, rank=2, text="Strong")
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(template=template)
    AnswerFactory.create(
        assessment=assessment,
        question=question,
        selected_option=option_low,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"question_{question.pk.hex}": str(option_high.pk)})

    answers = assessment.answers.filter(question=question)
    assert answers.count() == 1
    assert answers.get().selected_option == option_high


@pytest.mark.django_db
def test_answer_view_advances_draft_assessment_to_in_progress():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"question_{question.pk.hex}": str(option.pk)})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.IN_PROGRESS


@pytest.mark.django_db
def test_answer_view_leaves_in_progress_assessment_in_progress():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.IN_PROGRESS,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"question_{question.pk.hex}": str(option.pk)})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.IN_PROGRESS


@pytest.mark.django_db
def test_answer_view_complete_assessment_rejects_get_with_message_no_404():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.COMPLETE,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.get(url, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain
    messages = [str(m) for m in response.context["messages"]]
    assert any("complete" in m.lower() for m in messages)


@pytest.mark.django_db
def test_answer_view_complete_assessment_rejects_post_and_persists_nothing():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.COMPLETE,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    http_client.post(url, {f"question_{question.pk.hex}": str(option.pk)})

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    assert assessment.answers.count() == 0


@pytest.mark.django_db
def test_answer_view_prefills_previously_selected_answers():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(template=template)
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.get(url)

    initial = response.context["form"].initial
    assert initial[f"question_{question.pk.hex}"] == str(option.pk)


@pytest.mark.django_db
def test_answer_view_requires_login():
    assessment = AssessmentFactory.create()

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = Client().get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url


@pytest.mark.django_db
def test_answer_view_requires_login_even_when_assessment_is_complete():
    assessment = AssessmentFactory.create(status=Assessment.Status.COMPLETE)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = Client().get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url
    assert response.url != reverse("assessments:detail", kwargs={"pk": assessment.pk})


def test_entry_url_no_longer_registered():
    with pytest.raises(NoReverseMatch):
        reverse("assessments:entry", kwargs={"pk": uuid.uuid4()})
