import uuid
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.db import IntegrityError, transaction
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
    ClientAccessLinkFactory,
    QuestionFactory,
    QuestionOptionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import (
    Assessment,
    CategoryGuidance,
    ClientAccessLink,
)
from complete_business_analysis_tool.assessments.services import (
    assessment_completion_status,
    generate_client_access_link,
    is_client_access_link_valid,
    regenerate_client_access_link,
    revoke_client_access_link,
)
from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_assessment_name_defaults_to_initial_report():
    assessment = AssessmentFactory.create()
    assert assessment.name == "Initial Report"


@pytest.mark.django_db
def test_assessment_detail_lists_all_analysis_runs_with_status_and_timestamp():
    assessment = AssessmentFactory.create(status=Assessment.Status.COMPLETE)
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


@pytest.mark.django_db
def test_detail_hub_shows_guidance_and_answer_links_with_done_indicators():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.IN_PROGRESS,
        guidance_submitted_at=timezone.now(),
    )
    AnswerFactory.create(assessment=assessment, question=question)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert reverse("assessments:guidance", kwargs={"pk": assessment.pk}) in content
    assert reverse("assessments:answer", kwargs={"pk": assessment.pk}) in content
    expected_done_indicators = 2
    assert content.count("Done") == expected_done_indicators


@pytest.mark.django_db
def test_detail_hub_shows_not_done_indicators_when_guidance_and_answers_incomplete():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
        guidance_submitted_at=None,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    expected_not_done_indicators = 2
    assert content.count("Not done") == expected_not_done_indicators


@pytest.mark.django_db
def test_detail_hub_mark_complete_button_disabled_with_reason_when_ineligible():
    assessment = AssessmentFactory.create(
        status=Assessment.Status.IN_PROGRESS,
        guidance_submitted_at=None,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert "disabled" in content
    assert "Category Guidance has not been submitted." in content


@pytest.mark.django_db
def test_detail_hub_mark_complete_button_enabled_when_eligible():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.IN_PROGRESS,
        guidance_submitted_at=timezone.now(),
    )
    AnswerFactory.create(assessment=assessment, question=question)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert reverse("assessments:mark_complete", kwargs={"pk": assessment.pk}) in content
    assert "disabled" not in content


@pytest.mark.django_db
def test_mark_complete_rejects_when_ineligible_no_status_change_no_analysis():
    assessment = AssessmentFactory.create(
        status=Assessment.Status.IN_PROGRESS,
        guidance_submitted_at=None,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:mark_complete", kwargs={"pk": assessment.pk})
    response = http_client.post(url, follow=True)

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.IN_PROGRESS
    assert Analysis.objects.filter(assessment=assessment).count() == 0
    messages = [str(m) for m in response.context["messages"]]
    assert any("complete" in m.lower() for m in messages)


@pytest.mark.django_db
def test_mark_complete_sets_status_and_redirects_to_report_autostart_when_eligible():
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.IN_PROGRESS,
        guidance_submitted_at=timezone.now(),
    )
    AnswerFactory.create(assessment=assessment, question=question)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:mark_complete", kwargs={"pk": assessment.pk})
    response = http_client.post(url)

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    report_url = reverse("reports:report", kwargs={"pk": assessment.pk})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{report_url}?autostart=1"


@pytest.mark.django_db
def test_mark_complete_on_already_complete_assessment_does_not_retrigger_autostart():
    assessment = AssessmentFactory.create(
        status=Assessment.Status.COMPLETE,
        guidance_submitted_at=timezone.now(),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:mark_complete", kwargs={"pk": assessment.pk})
    response = http_client.post(url)

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    report_url = reverse("reports:report", kwargs={"pk": assessment.pk})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == report_url


@pytest.mark.django_db
def test_mark_complete_requires_login():
    assessment = AssessmentFactory.create()

    url = reverse("assessments:mark_complete", kwargs={"pk": assessment.pk})
    response = Client().post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url


@pytest.mark.django_db
def test_complete_detail_shows_category_guidance_alongside_answers():
    category_with_guidance = CategoryFactory.create(name="Alpha")
    category_without_guidance = CategoryFactory.create(name="Bravo")
    question_a = QuestionFactory.create(category=category_with_guidance)
    question_b = QuestionFactory.create(category=category_without_guidance)
    assessment = AssessmentFactory.create(status=Assessment.Status.COMPLETE)
    AnswerFactory.create(assessment=assessment, question=question_a)
    AnswerFactory.create(assessment=assessment, question=question_b)
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category_with_guidance,
        text="Focus on scaling the sales team.",
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert "Focus on scaling the sales team." in content
    groups = {g["name"]: g for g in response.context["grouped_answers"]}
    assert groups["Alpha"]["guidance"] == "Focus on scaling the sales team."
    assert groups["Bravo"]["guidance"] is None


@pytest.mark.django_db
def test_complete_detail_keeps_same_named_categories_separate():
    category_1 = CategoryFactory.create(name="Sales")
    category_2 = CategoryFactory.create(name="Sales")
    question_1 = QuestionFactory.create(category=category_1)
    question_2 = QuestionFactory.create(category=category_2)
    assessment = AssessmentFactory.create(status=Assessment.Status.COMPLETE)
    AnswerFactory.create(assessment=assessment, question=question_1)
    AnswerFactory.create(assessment=assessment, question=question_2)
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category_1,
        text="Guidance for the first Sales category.",
    )
    CategoryGuidanceFactory.create(
        assessment=assessment,
        category=category_2,
        text="Guidance for the second Sales category.",
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)

    groups = response.context["grouped_answers"]
    expected_group_count = 2
    assert len(groups) == expected_group_count
    guidance_texts = {g["guidance"] for g in groups}
    assert guidance_texts == {
        "Guidance for the first Sales category.",
        "Guidance for the second Sales category.",
    }


@pytest.mark.django_db
def test_client_access_link_unique_per_assessment_and_link_type():
    assessment = AssessmentFactory.create()
    ClientAccessLinkFactory.create(
        assessment=assessment,
        link_type=ClientAccessLink.LinkType.GUIDANCE,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ClientAccessLinkFactory.create(
            assessment=assessment,
            link_type=ClientAccessLink.LinkType.GUIDANCE,
        )


@pytest.mark.django_db
def test_generate_client_access_link_creates_active_row_when_none_exists():
    assessment = AssessmentFactory.create()

    link = generate_client_access_link(assessment, ClientAccessLink.LinkType.GUIDANCE)

    assert link.status == ClientAccessLink.Status.ACTIVE
    assert link.token
    assert (
        ClientAccessLink.objects.filter(
            assessment=assessment,
            link_type=ClientAccessLink.LinkType.GUIDANCE,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_generate_client_access_link_leaves_active_row_unchanged():
    existing = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)

    link = generate_client_access_link(existing.assessment, existing.link_type)

    assert link.pk == existing.pk
    assert link.token == existing.token
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_generate_client_access_link_reissues_token_when_revoked():
    existing = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.REVOKED)
    original_token = existing.token

    link = generate_client_access_link(existing.assessment, existing.link_type)

    assert link.pk == existing.pk
    assert link.token != original_token
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_revoke_client_access_link_marks_revoked_without_new_token():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)
    original_token = link.token

    revoked = revoke_client_access_link(link)

    assert revoked.status == ClientAccessLink.Status.REVOKED
    assert revoked.token == original_token


@pytest.mark.django_db
def test_regenerate_client_access_link_overwrites_token_and_stays_active():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)
    original_token = link.token

    regenerated = regenerate_client_access_link(link)

    assert regenerated.token != original_token
    assert regenerated.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_regenerate_client_access_link_reactivates_a_revoked_link():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.REVOKED)

    regenerated = regenerate_client_access_link(link)

    assert regenerated.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_is_client_access_link_valid_false_for_unrecognized_token():
    assert is_client_access_link_valid("not-a-real-token") is False


@pytest.mark.django_db
def test_is_client_access_link_valid_false_when_revoked():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.REVOKED,
        assessment=AssessmentFactory.create(status=Assessment.Status.IN_PROGRESS),
    )

    assert is_client_access_link_valid(link.token) is False


@pytest.mark.django_db
def test_is_client_access_link_valid_false_when_assessment_complete():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.COMPLETE),
    )

    assert is_client_access_link_valid(link.token) is False


@pytest.mark.django_db
def test_is_client_access_link_valid_true_when_active_and_assessment_not_complete():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.IN_PROGRESS),
    )

    assert is_client_access_link_valid(link.token) is True


@pytest.mark.django_db
def test_access_link_generate_requires_login():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = Client().post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url
    assert not ClientAccessLink.objects.exists()


@pytest.mark.django_db
def test_access_link_revoke_requires_login():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)

    url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = Client().post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url
    link.refresh_from_db()
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_access_link_regenerate_requires_login():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)
    original_token = link.token

    url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = Client().post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert "/login/" in response.url or "accounts/login" in response.url
    link.refresh_from_db()
    assert link.token == original_token


@pytest.mark.django_db
def test_access_link_generate_creates_active_row_and_redirects_to_detail():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("assessments:detail", kwargs={"pk": assessment.pk})
    link = ClientAccessLink.objects.get(assessment=assessment, link_type="guidance")
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_access_link_generate_redirects_to_next_when_provided():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    guidance_url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = http_client.post(url, {"next": guidance_url})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == guidance_url


@pytest.mark.django_db
def test_access_link_generate_ignores_next_pointing_off_site():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = http_client.post(url, {"next": "https://evil.example.com/steal"})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("assessments:detail", kwargs={"pk": assessment.pk})


@pytest.mark.django_db
def test_access_link_generate_rejected_when_client_has_no_email():
    assessment = AssessmentFactory.create(client=ClientFactory.create(email=""))
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = http_client.post(url, follow=True)

    assert not ClientAccessLink.objects.exists()
    messages = [str(m) for m in response.context["messages"]]
    assert any("email" in m.lower() for m in messages)


@pytest.mark.django_db
def test_access_link_generate_rejected_when_assessment_complete():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
        status=Assessment.Status.COMPLETE,
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    response = http_client.post(url, follow=True)

    assert not ClientAccessLink.objects.exists()
    messages = [str(m) for m in response.context["messages"]]
    assert any("complete" in m.lower() for m in messages)


@pytest.mark.django_db
def test_access_link_revoke_marks_existing_link_revoked():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)
    original_token = link.token
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    link.refresh_from_db()
    assert link.status == ClientAccessLink.Status.REVOKED
    assert link.token == original_token


@pytest.mark.django_db
def test_access_link_revoke_rejected_when_assessment_complete():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.COMPLETE),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    http_client.post(url)

    link.refresh_from_db()
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_access_link_regenerate_overwrites_token_and_stays_active():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.ACTIVE)
    original_token = link.token
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    link.refresh_from_db()
    assert link.token != original_token
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_access_link_regenerate_rejected_when_assessment_complete():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.COMPLETE),
    )
    original_token = link.token
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    http_client.post(url)

    link.refresh_from_db()
    assert link.token == original_token


@pytest.mark.django_db
def test_access_link_regenerate_404s_on_revoked_link():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.REVOKED)
    original_token = link.token
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    link.refresh_from_db()
    assert link.status == ClientAccessLink.Status.REVOKED
    assert link.token == original_token


@pytest.mark.django_db
def test_access_link_revoke_404s_on_already_revoked_link():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.REVOKED)
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": link.link_type},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_access_link_unknown_link_type_404s():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "bogus"},
    )
    response = http_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_detail_hub_shows_generate_button_for_client_with_email():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    generate_guidance_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    generate_answer_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "answer"},
    )
    assert generate_guidance_url in content
    assert generate_answer_url in content


@pytest.mark.django_db
def test_detail_hub_shows_client_edit_link_when_client_has_no_email():
    assessment = AssessmentFactory.create(client=ClientFactory.create(email=""))
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    edit_url = reverse("clients:edit", kwargs={"pk": assessment.client.pk})
    generate_guidance_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    expected_edit_link_count = 2
    assert content.count(edit_url) == expected_edit_link_count
    assert generate_guidance_url not in content


@pytest.mark.django_db
def test_detail_hub_shows_copy_revoke_regenerate_for_active_link():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        link_type=ClientAccessLink.LinkType.GUIDANCE,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(email="c@example.com"),
        ),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": link.assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    revoke_url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    regenerate_url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    assert link.token in content
    assert revoke_url in content
    assert regenerate_url in content


@pytest.mark.django_db
def test_detail_hub_revoke_returns_control_to_generate_state():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        link_type=ClientAccessLink.LinkType.GUIDANCE,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(email="c@example.com"),
        ),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    revoke_url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    http_client.post(revoke_url)

    url = reverse("assessments:detail", kwargs={"pk": link.assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    generate_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    assert generate_url in content
    assert link.token not in content


@pytest.mark.django_db
def test_detail_hub_regenerate_reflects_new_url_immediately():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        link_type=ClientAccessLink.LinkType.GUIDANCE,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(email="c@example.com"),
        ),
    )
    original_token = link.token
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    regenerate_url = reverse(
        "assessments:access_link_regenerate",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    http_client.post(regenerate_url)

    url = reverse("assessments:detail", kwargs={"pk": link.assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    link.refresh_from_db()
    assert link.token in content
    assert original_token not in content


@pytest.mark.django_db
def test_detail_hub_hides_access_link_controls_once_assessment_complete():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        link_type=ClientAccessLink.LinkType.GUIDANCE,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(email="c@example.com"),
            status=Assessment.Status.COMPLETE,
        ),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": link.assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    generate_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    revoke_url = reverse(
        "assessments:access_link_revoke",
        kwargs={"pk": link.assessment.pk, "link_type": "guidance"},
    )
    assert generate_url not in content
    assert revoke_url not in content
    assert link.token not in content


@pytest.mark.django_db
def test_guidance_page_shows_only_guidance_access_link_controls():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:guidance", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    generate_guidance_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    generate_answer_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "answer"},
    )
    assert generate_guidance_url in content
    assert generate_answer_url not in content


@pytest.mark.django_db
def test_answer_page_shows_only_answer_access_link_controls():
    assessment = AssessmentFactory.create(
        client=ClientFactory.create(email="c@example.com"),
    )
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:answer", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    generate_guidance_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "guidance"},
    )
    generate_answer_url = reverse(
        "assessments:access_link_generate",
        kwargs={"pk": assessment.pk, "link_type": "answer"},
    )
    assert generate_answer_url in content
    assert generate_guidance_url not in content
