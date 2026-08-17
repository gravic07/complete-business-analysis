from decimal import Decimal

import pytest

from complete_business_analysis_tool.analysis.models import Analysis
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
    CategoryRecommendations,
    CategorySection,
    ExecutiveSummary,
    Feedback,
    RecommendationsOverview,
)


@pytest.mark.django_db
def test_orchestrator_calls_generate_category_section_not_generate_section(monkeypatch):
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

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert len(cat_calls) == 1
    assert "answers" in cat_calls[0]


@pytest.mark.django_db
def test_orchestrator_calls_generate_executive_summary_with_category_sections(
    monkeypatch,
):
    overall_calls = []

    def capture_overall(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "cat content", "impact": "", "path_forward": ""},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        capture_overall,
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert len(overall_calls) == 1
    call_kwargs = overall_calls[0]
    assert "category_sections" in call_kwargs
    assert isinstance(call_kwargs["category_sections"], dict)
    assert category.name in call_kwargs["category_sections"]


def _make_two_category_assessment():
    cat_a = CategoryFactory.create(name="Alpha")
    cat_b = CategoryFactory.create(name="Beta")
    q_a = QuestionFactory.create(category=cat_a)
    q_b = QuestionFactory.create(category=cat_b)
    opt_a = QuestionOptionFactory.create(question=q_a, rank=1, weight=Decimal("1.0000"))
    opt_b = QuestionOptionFactory.create(question=q_b, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=q_a, selected_option=opt_a)
    AnswerFactory.create(assessment=assessment, question=q_b, selected_option=opt_b)
    return assessment, cat_a, cat_b


@pytest.mark.django_db
def test_second_run_overall_assembled_from_all_categories_including_prior_runs(
    monkeypatch,
):
    call_count = [0]

    def category_stub(**kwargs):
        call_count[0] += 1
        return {
            "overview": f"cat-content-{call_count[0]}",
            "impact": "",
            "path_forward": "",
        }

    overall_calls = []

    def overall_stub(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        category_stub,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        overall_stub,
    )

    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    cat_b_section = CategorySection.objects.get(analysis=analysis1, category=cat_b)

    # Second run: only cat_a in scope (category-only feedback)
    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(
        feedback=feedback,
        category=cat_a,
        text="Revise Alpha.",
    )
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)

    overall_calls.clear()
    run_analysis(analysis2.pk)

    assert len(overall_calls) == 1
    sections_passed = overall_calls[0]["category_sections"]
    assert cat_a.name in sections_passed
    assert cat_b.name in sections_passed
    # cat_b's content must come from the first run's section (unchanged)
    assert cat_b_section.overview in sections_passed[cat_b.name]


@pytest.mark.django_db
def test_task_creates_one_report_section_per_category_plus_overall(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "Generated narrative",
            "impact": "",
            "path_forward": "",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "Generated narrative",
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=3,
        weight=Decimal("2.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert CategorySection.objects.filter(analysis=analysis, category=category).exists()
    assert ExecutiveSummary.objects.filter(analysis=analysis).exists()
    assert CategorySection.objects.filter(analysis=analysis).count() == 1


@pytest.mark.django_db
def test_task_creates_separate_sections_for_two_categories(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "Generated narrative",
            "impact": "",
            "path_forward": "",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "Generated narrative",
    )

    cat_a = CategoryFactory.create()
    cat_b = CategoryFactory.create()
    assessment = AssessmentFactory.create()

    for cat in (cat_a, cat_b):
        q = QuestionFactory.create(category=cat)
        opt = QuestionOptionFactory.create(question=q, rank=2, weight=Decimal("1.0000"))
        AnswerFactory.create(assessment=assessment, question=q, selected_option=opt)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert CategorySection.objects.filter(analysis=analysis, category=cat_a).exists()
    assert CategorySection.objects.filter(analysis=analysis, category=cat_b).exists()
    assert ExecutiveSummary.objects.filter(analysis=analysis).exists()
    expected_cnt = 2
    assert CategorySection.objects.filter(analysis=analysis).count() == expected_cnt


@pytest.mark.django_db
def test_report_sections_are_never_updated_after_creation(monkeypatch):
    call_count = 0

    def counting_client(**kwargs):
        nonlocal call_count
        call_count += 1
        return {"overview": f"Run {call_count}", "impact": "", "path_forward": ""}

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        counting_client,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    first_overview = CategorySection.objects.get(
        analysis=analysis1,
        category=category,
    ).overview

    analysis2 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis2.pk)

    # Original section is unchanged
    assert (
        CategorySection.objects.get(analysis=analysis1, category=category).overview
        == first_overview
    )
    # New analysis has its own sections
    assert CategorySection.objects.filter(analysis=analysis2, category=category).exists()
    assert ExecutiveSummary.objects.filter(analysis=analysis2).exists()


@pytest.mark.django_db
def test_executive_summary_receives_labeled_concatenated_text_per_category(monkeypatch):
    overall_calls = []

    def capture_overall(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {
            "overview": "the overview",
            "impact": "the impact",
            "path_forward": "the path forward",
        },
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        capture_overall,
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert len(overall_calls) == 1
    text = overall_calls[0]["category_sections"][category.name]
    assert "the overview" in text
    assert "the impact" in text
    assert "the path forward" in text
    assert "Overview:" in text
    assert "Impact:" in text
    assert "Path Forward:" in text


@pytest.mark.django_db
def test_prior_section_fields_passed_on_reanalysis(monkeypatch):
    cat_calls = []

    def capture_category(**kwargs):
        cat_calls.append(kwargs)
        return {"overview": f"run-{len(cat_calls)}", "impact": "i", "path_forward": "p"}

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        capture_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    analysis2 = Analysis.objects.create(assessment=assessment)
    cat_calls.clear()
    run_analysis(analysis2.pk)

    assert len(cat_calls) == 1
    call = cat_calls[0]
    assert call["prior_overview"] == "run-1"
    assert call["prior_impact"] == "i"
    assert call["prior_path_forward"] == "p"


@pytest.mark.django_db
def test_report_feedback_flows_to_ai_service_calls(monkeypatch):
    cat_calls = []
    overall_calls = []

    def capture_category(**kwargs):
        cat_calls.append(kwargs)
        return {"overview": "o", "impact": "i", "path_forward": "p"}

    def capture_overall(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        capture_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        capture_overall,
    )

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    feedback = Feedback.objects.create(
        assessment=assessment,
        report_feedback="Global feedback text.",
    )
    analysis = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis.pk)

    assert "Global feedback text." in cat_calls[0]["feedback_text"]


# --- CategoryRecommendations orchestrator tests ---


def _patch_ai(monkeypatch, cat_recs_return=None):
    """Monkeypatch all AI functions; returns a list that collects rec calls."""
    if cat_recs_return is None:
        cat_recs_return = ["r1", "r2", "r3", "r4", "r5", "r6", "r7"]
    rec_calls = []

    def capture_recs(**kwargs):
        rec_calls.append(kwargs)
        return list(cat_recs_return)

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: {"overview": "o", "impact": "i", "path_forward": "p"},
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_executive_summary",
        lambda **kwargs: "overall",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_recommendations",
        capture_recs,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_recommendations_overview",
        lambda **kwargs: "recommendations overview",
    )
    return rec_calls


@pytest.mark.django_db
def test_orchestrator_creates_one_category_recommendations_per_category(monkeypatch):
    _patch_ai(monkeypatch)

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert CategoryRecommendations.objects.filter(
        analysis=analysis,
        category=category,
    ).exists()
    assert CategoryRecommendations.objects.filter(analysis=analysis).count() == 1


@pytest.mark.django_db
def test_orchestrator_category_recommendations_idempotent(monkeypatch):
    _patch_ai(monkeypatch)

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    run_analysis(analysis.pk)

    assert CategoryRecommendations.objects.filter(analysis=analysis).count() == 1


@pytest.mark.django_db
def test_orchestrator_partial_reanalysis_creates_recommendations_only_for_in_scope(
    monkeypatch,
):
    rec_calls = _patch_ai(monkeypatch)

    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    rec_calls.clear()

    # Second run: only cat_a in scope
    feedback = Feedback.objects.create(assessment=assessment)
    CategoryFeedback.objects.create(feedback=feedback, category=cat_a, text="Revise.")
    analysis2 = Analysis.objects.create(assessment=assessment, feedback=feedback)
    run_analysis(analysis2.pk)

    # Only one new CategoryRecommendations created (for cat_a)
    assert CategoryRecommendations.objects.filter(analysis=analysis2).count() == 1
    assert CategoryRecommendations.objects.filter(
        analysis=analysis2,
        category=cat_a,
    ).exists()
    assert not CategoryRecommendations.objects.filter(
        analysis=analysis2,
        category=cat_b,
    ).exists()


# --- RecommendationsOverview orchestrator tests ---


@pytest.mark.django_db
def test_orchestrator_creates_one_recommendations_overview_per_analysis(monkeypatch):
    _patch_ai(monkeypatch)

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert RecommendationsOverview.objects.filter(analysis=analysis).count() == 1


@pytest.mark.django_db
def test_orchestrator_recommendations_overview_idempotent(monkeypatch):
    _patch_ai(monkeypatch)

    category = CategoryFactory.create()
    question = QuestionFactory.create(category=category)
    option = QuestionOptionFactory.create(
        question=question,
        rank=1,
        weight=Decimal("1.0000"),
    )
    assessment = AssessmentFactory.create()
    AnswerFactory.create(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)
    run_analysis(analysis.pk)

    assert RecommendationsOverview.objects.filter(analysis=analysis).count() == 1
