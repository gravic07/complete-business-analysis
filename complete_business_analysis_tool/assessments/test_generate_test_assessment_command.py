from io import StringIO

import pytest
from django.core.management import call_command

from complete_business_analysis_tool.assessments.factories import (
    AssessmentTemplateFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import Answer, Assessment


@pytest.mark.django_db
def test_command_creates_in_progress_assessment_with_no_guidance(monkeypatch):
    template = AssessmentTemplateFactory.create()
    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    for rank in range(1, 6):
        QuestionOptionFactory.create(question=question, rank=rank)
    TemplateQuestionFactory.create(template=template, question=question)

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

    out = StringIO()
    call_command("generate_test_assessment", stdout=out)

    assessment = Assessment.objects.get(template=template)
    assert assessment.status == Assessment.Status.IN_PROGRESS
    assert assessment.guidance_submitted_at is None
    assert Answer.objects.filter(assessment=assessment).count() == 1
    assert "Guidance:    not yet entered" in out.getvalue()
