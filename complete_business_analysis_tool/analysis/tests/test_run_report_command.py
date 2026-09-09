from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    QuestionFactory,
    TemplateQuestionFactory,
)
from complete_business_analysis_tool.assessments.models import Assessment


def _run(assessment_id: str) -> str:
    out = StringIO()
    call_command("run_report", assessment_id, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_unanswered_questions_raise_and_create_no_analysis():
    assessment = AssessmentFactory.create()
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)

    with pytest.raises(CommandError, match="unanswered questions"):
        _run(str(assessment.pk))

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.DRAFT
    assert assessment.guidance_submitted_at is None
    assert not Analysis.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_missing_guidance_is_treated_as_empty_and_status_progresses():
    assessment = AssessmentFactory.create(status=Assessment.Status.IN_PROGRESS)
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)
    AnswerFactory.create(assessment=assessment, question=question)

    output = _run(str(assessment.pk))

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    assert assessment.guidance_submitted_at is not None
    assert "treating as intentionally empty" in output
    assert Analysis.objects.filter(assessment=assessment).exists()


@pytest.mark.django_db
def test_already_complete_assessment_is_unchanged():
    assessment = AssessmentFactory.create(
        status=Assessment.Status.COMPLETE,
        guidance_submitted_at=timezone.now(),
    )
    question = QuestionFactory.create()
    TemplateQuestionFactory.create(template=assessment.template, question=question)
    AnswerFactory.create(assessment=assessment, question=question)
    guidance_time = assessment.guidance_submitted_at

    output = _run(str(assessment.pk))

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.COMPLETE
    assert assessment.guidance_submitted_at == guidance_time
    assert "treating as intentionally empty" not in output
    # The only "→" expected is the "Analysis: <pk> → running..." line;
    # no status-transition line should be printed since nothing changed.
    assert output.count("→") == 1
