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
    CategorySection,
    ExecutiveSummary,
    Feedback,
    Roadmap,
)
from complete_business_analysis_tool.reports.queries import latest_roadmap


@pytest.mark.django_db
def test_analysis_starts_in_pending_status():
    assessment = AssessmentFactory()
    analysis = Analysis.objects.create(assessment=assessment)
    assert analysis.status == Analysis.Status.PENDING


@pytest.mark.django_db
def test_run_analysis_task_transitions_to_complete(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "stub", "impact": "stub", "path_forward": "stub"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
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
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "stub", "impact": "stub", "path_forward": "stub"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
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
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "cat stub",
            "impact": "cat stub",
            "path_forward": "cat stub",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall stub",
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

    # Only cat_a gets new category records in analysis2
    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert not CategoryScore.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert CategorySection.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert not CategorySection.objects.filter(analysis=analysis2, category=cat_b).exists()
    # Overall is always regenerated
    assert ExecutiveSummary.objects.filter(analysis=analysis2).exists()


@pytest.mark.django_db
def test_reanalysis_with_overall_feedback_creates_records_for_all_categories(
    monkeypatch,
):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "cat stub",
            "impact": "cat stub",
            "path_forward": "cat stub",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall stub",
    )
    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    feedback = Feedback.objects.create(
        assessment=assessment,
        report_feedback="Everything needs rethinking.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert CategoryScore.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert CategorySection.objects.filter(analysis=analysis2, category=cat_a).exists()
    assert CategorySection.objects.filter(analysis=analysis2, category=cat_b).exists()
    assert ExecutiveSummary.objects.filter(analysis=analysis2).exists()


@pytest.mark.django_db
def test_reanalysis_passes_prior_section_content_to_generate_category_section(
    monkeypatch,
):
    cat_call_log = []

    def capture_category(**kwargs):
        cat_call_log.append(kwargs)
        return {"overview": "cat content", "impact": "", "path_forward": ""}

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        capture_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )
    assessment, cat_a, _ = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    cat_call_log.clear()

    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(
        feedback=feedback,
        category=cat_a,
        text="Revise this.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    # Only cat_a is regenerated; verify prior overview was passed
    assert len(cat_call_log) == 1
    assert cat_call_log[0]["prior_overview"] == "cat content"


@pytest.mark.django_db
def test_category_only_feedback_always_creates_overall_section(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "cat stub",
            "impact": "cat stub",
            "path_forward": "cat stub",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall stub",
    )
    assessment, cat_a, _cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(
        feedback=feedback,
        category=cat_a,
        text="Improve Alpha.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    assert ExecutiveSummary.objects.filter(analysis=analysis2).exists()


# ---------------------------------------------------------------------------
# Issue 04 — Idempotency
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rerunning_same_analysis_does_not_create_duplicate_sections(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "stub", "impact": "stub", "path_forward": "stub"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "stub",
    )
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    section_count_after_first_run = (
        CategorySection.objects.filter(analysis=analysis).count()
        + ExecutiveSummary.objects.filter(analysis=analysis).count()
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    assert (
        CategorySection.objects.filter(analysis=analysis).count()
        + ExecutiveSummary.objects.filter(analysis=analysis).count()
        == section_count_after_first_run
    )


@pytest.mark.django_db
def test_preexisting_category_section_is_skipped_on_retry(monkeypatch):
    cat_calls = []

    def capture_category(**kwargs):
        cat_calls.append(kwargs)
        return {"overview": "generated", "impact": "", "path_forward": ""}

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        capture_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )
    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis = Analysis.objects.create(assessment=assessment)
    # Simulate partial failure: cat_a was completed before the crash
    CategorySection.objects.create(
        analysis=analysis,
        category=cat_a,
        overview="pre-existing",
        impact="",
        path_forward="",
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    # AI was called only for cat_b (cat_a already had a section)
    assert len(cat_calls) == 1
    # The pre-existing cat_a section is preserved untouched
    assert (
        CategorySection.objects.get(analysis=analysis, category=cat_a).overview
        == "pre-existing"
    )
    # cat_b section was generated
    assert CategorySection.objects.filter(analysis=analysis, category=cat_b).exists()


@pytest.mark.django_db
def test_failed_analysis_transitions_back_to_processing_on_retry(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "stub", "impact": "stub", "path_forward": "stub"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "stub",
    )
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.FAILED,
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE


@pytest.mark.django_db
def test_preexisting_overall_section_is_skipped_on_retry(monkeypatch):
    overall_calls = []

    def capture_overall(**kwargs):
        overall_calls.append(kwargs)
        return "new overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "cat stub",
            "impact": "cat stub",
            "path_forward": "cat stub",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        capture_overall,
    )
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    # Simulate partial failure: all category sections done, overall not yet created
    CategorySection.objects.create(
        analysis=analysis,
        category=category,
        overview="cat pre-existing",
        impact="",
        path_forward="",
    )
    ExecutiveSummary.objects.create(
        analysis=analysis,
        content="overall pre-existing",
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    # Overall AI was never called
    assert len(overall_calls) == 0
    # Overall section content is unchanged
    assert (
        ExecutiveSummary.objects.get(analysis=analysis).content == "overall pre-existing"
    )


# ---------------------------------------------------------------------------
# Roadmap pipeline integration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_run_analysis_creates_roadmap():
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    assert Roadmap.objects.filter(analysis=analysis).count() == 1


@pytest.mark.django_db
def test_roadmap_has_twelve_months_with_non_empty_lists():
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    roadmap = Roadmap.objects.get(analysis=analysis)
    assert len(roadmap.months) == 12  # noqa: PLR2004
    for month in roadmap.months:
        assert month["goals"]
        assert month["action_items"]
        assert month["challenges"]


@pytest.mark.django_db
def test_second_analysis_run_creates_new_roadmap():
    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    feedback = Feedback.objects.create(assessment=assessment, report_feedback="Redo it.")
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    assert Roadmap.objects.filter(analysis=analysis1).exists()
    assert Roadmap.objects.filter(analysis=analysis2).exists()
    assert latest_roadmap(assessment).analysis_id == analysis2.pk


@pytest.mark.django_db
def test_partial_reanalysis_creates_roadmap():
    assessment, cat_a, _cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    # Feedback only on one category — partial re-analysis scope
    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(feedback=feedback, category=cat_a, text="Focus here.")
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    analysis2.refresh_from_db()
    assert analysis2.status == Analysis.Status.COMPLETE
    assert Roadmap.objects.filter(analysis=analysis2).exists()


@pytest.mark.django_db
def test_preexisting_roadmap_is_skipped_on_retry(monkeypatch):
    roadmap_calls = []

    def capture_roadmap(**kwargs):
        roadmap_calls.append(kwargs)
        return {
            "months": [
                {"goals": ["g"], "action_items": ["a"], "challenges": ["c"]}
                for _ in range(12)
            ],
            "potential_challenges": ["p"],
            "post_implementation_outcomes": ["o"],
            "closing_reflections": ["r"],
        }

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_roadmap",
        capture_roadmap,
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    # Simulate retry: Roadmap already written before the crash
    Roadmap.objects.create(
        analysis=analysis,
        months=[
            {"goals": ["pre-existing"], "action_items": [], "challenges": []}
            for _ in range(12)
        ],
        potential_challenges=[],
        post_implementation_outcomes=[],
        closing_reflections=[],
    )

    run_analysis(analysis.pk)

    analysis.refresh_from_db()
    assert analysis.status == Analysis.Status.COMPLETE
    assert Roadmap.objects.filter(analysis=analysis).count() == 1
    assert len(roadmap_calls) == 0
    assert Roadmap.objects.get(analysis=analysis).months[0]["goals"] == ["pre-existing"]
