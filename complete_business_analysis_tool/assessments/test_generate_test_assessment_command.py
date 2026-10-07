from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from complete_business_analysis_tool.assessments.factories import (
    AssessmentTemplateFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import Answer, Assessment
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.fixture
def template(db):
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    for rank in range(1, 6):
        QuestionOptionFactory.create(question=question, rank=rank)
    TemplateQuestionFactory.create(template=template, question=question)
    return template


@pytest.fixture
def _answer_prompts(monkeypatch):
    responses = iter(
        [
            "Acme Co",  # business name
            "Jane",  # first name
            "Doe",  # last name
            "CEO",  # title
            "1",  # industry
            "1",  # company size
            "1",  # revenue
            "1",  # corporate style
            "1",  # template selection (only one exists)
            "7",  # category rating
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))


@pytest.mark.usefixtures("_answer_prompts")
def test_command_creates_in_progress_assessment_with_no_guidance(template):
    UserFactory.create(is_superuser=True)

    out = StringIO()
    call_command("generate_test_assessment", stdout=out)

    assessment = Assessment.objects.get(template=template)
    assert assessment.status == Assessment.Status.IN_PROGRESS
    assert assessment.guidance_submitted_at is None
    assert Answer.objects.filter(assessment=assessment).count() == 1
    assert "Guidance:    not yet entered" in out.getvalue()


@pytest.mark.usefixtures("_answer_prompts")
def test_command_stamps_user_given_by_email(template):
    UserFactory.create(is_superuser=True)
    user = UserFactory.create(email="advisor@example.com")

    call_command(
        "generate_test_assessment",
        user="advisor@example.com",
        stdout=StringIO(),
    )

    assessment = Assessment.objects.get(template=template)
    assert assessment.created_by == user
    assert assessment.client.created_by == user
    assert assessment.client.team == user.team


@pytest.mark.usefixtures("_answer_prompts")
def test_command_defaults_to_earliest_created_superuser(template):
    now = timezone.now()
    UserFactory.create(date_joined=now - timedelta(days=3))
    earliest_superuser = UserFactory.create(
        is_superuser=True,
        date_joined=now - timedelta(days=2),
    )
    UserFactory.create(is_superuser=True, date_joined=now - timedelta(days=1))

    call_command("generate_test_assessment", stdout=StringIO())

    assessment = Assessment.objects.get(template=template)
    assert assessment.created_by == earliest_superuser
    assert assessment.client.team == earliest_superuser.team


@pytest.mark.django_db
def test_command_errors_when_no_superuser_exists():
    UserFactory.create()

    with pytest.raises(CommandError, match="superuser"):
        call_command("generate_test_assessment", stdout=StringIO())


@pytest.mark.django_db
def test_command_errors_when_user_email_not_found():
    with pytest.raises(CommandError, match=r"nobody@example\.com"):
        call_command(
            "generate_test_assessment",
            user="nobody@example.com",
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_command_errors_when_user_has_no_team():
    UserFactory.create(email="loner@example.com", team=None)

    with pytest.raises(CommandError, match="Team"):
        call_command(
            "generate_test_assessment",
            user="loner@example.com",
            stdout=StringIO(),
        )
