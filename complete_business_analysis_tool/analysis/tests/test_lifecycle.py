from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from complete_business_analysis_tool.analysis.models import Analysis, CategoryScore
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
)
from complete_business_analysis_tool.reports.models import (
    CategoryFeedback,
    Feedback,
    ReportSection,
)


@pytest.mark.django_db
def test_analysis_starts_in_pending_status():
    assessment = AssessmentFactory()
    analysis = Analysis.objects.create(assessment=assessment)
    assert analysis.status == Analysis.Status.PENDING


@pytest.mark.django_db
def test_run_analysis_task_transitions_to_complete(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        lambda **kwargs: "stub",
    )
    assessment = AssessmentFactory()
    analysis = Analysis.objects.create(assessment=assessment)

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE


@pytest.mark.django_db
def test_cannot_create_second_active_analysis_for_same_assessment():
    assessment = AssessmentFactory()
    Analysis.objects.create(assessment=assessment, status=Analysis.Status.PENDING)

    duplicate = Analysis(assessment=assessment, status=Analysis.Status.PENDING)
    with pytest.raises(ValidationError):
        duplicate.full_clean()


@pytest.mark.django_db
def test_task_persists_category_scores_and_total(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        lambda **kwargs: "stub",
    )
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=3, weight=Decimal("2.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    assert analysis.total_score == Decimal("6.0000")  # 3 x 2.0
    score = CategoryScore.objects.get(analysis=analysis, category=category)
    assert score.score == Decimal("6.0000")
    assert score.max_possible_score == Decimal(
        "6.0000",
    )  # max_rank also 3 (only option)


@pytest.mark.django_db
def test_run_analysis_task_transitions_to_failed_on_error(monkeypatch):
    assessment = AssessmentFactory()
    analysis = Analysis.objects.create(assessment=assessment)

    def boom():
        msg = "AI exploded"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks._run_analysis_work",
        lambda analysis: boom(),
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.FAILED


def _make_two_category_assessment():
    """Assessment with two categories, one question + answer each."""
    cat_a = CategoryFactory(name="Alpha")
    cat_b = CategoryFactory(name="Beta")
    q_a = QuestionFactory(category=cat_a)
    q_b = QuestionFactory(category=cat_b)
    opt_a = QuestionOptionFactory(question=q_a, rank=1, weight=Decimal("1.0000"))
    opt_b = QuestionOptionFactory(question=q_b, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=q_a, selected_option=opt_a)
    AnswerFactory(assessment=assessment, question=q_b, selected_option=opt_b)
    return assessment, cat_a, cat_b


@pytest.mark.django_db
def test_reanalysis_with_category_feedback_only_creates_records_for_in_scope_category(
    monkeypatch,
):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        lambda **kwargs: f"Section for {kwargs['scope_label']}",
    )
    assessment, cat_a, cat_b = _make_two_category_assessment()

    # First full analysis run
    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    # Feedback only on cat_a
    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(
        feedback=feedback,
        category=cat_a,
        text="Improve Alpha.",
    )

    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    # Only cat_a gets new records in analysis2
    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert not CategoryScore.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert ReportSection.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert not ReportSection.objects.filter(analysis=analysis2, category=cat_b).exists()
    # No new overall section for category-only feedback
    assert not ReportSection.objects.filter(analysis=analysis2, category=None).exists()


@pytest.mark.django_db
def test_reanalysis_with_overall_feedback_creates_records_for_all_categories(
    monkeypatch,
):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        lambda **kwargs: f"Section for {kwargs['scope_label']}",
    )
    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    feedback = Feedback.objects.create(
        assessment=assessment,
        overall_text="Everything needs rethinking.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert ReportSection.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert ReportSection.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert ReportSection.objects.filter(analysis=analysis2, category=None).exists()


@pytest.mark.django_db
def test_reanalysis_passes_prior_section_content_to_generate_section(monkeypatch):
    call_log = []

    def capture_generate(**kwargs):
        call_log.append(kwargs)
        return f"Section for {kwargs['scope_label']}"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        capture_generate,
    )
    assessment, cat_a, _ = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    call_log.clear()

    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(
        feedback=feedback,
        category=cat_a,
        text="Revise this.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    alpha_call = next(c for c in call_log if c["scope_label"] == "Alpha")
    assert alpha_call["prior_content"] == "Section for Alpha"
