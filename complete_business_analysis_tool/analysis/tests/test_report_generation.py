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
    Feedback,
    ReportSection,
)


@pytest.mark.django_db
def test_orchestrator_calls_generate_category_section_not_generate_section(monkeypatch):
    cat_calls = []

    def capture_category(**kwargs):
        cat_calls.append(kwargs)
        return "generated"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        capture_category,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "overall",
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert len(cat_calls) == 1
    assert "answers" in cat_calls[0]


@pytest.mark.django_db
def test_orchestrator_calls_generate_overall_section_with_category_sections(monkeypatch):
    overall_calls = []

    def capture_overall(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: "cat content",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        capture_overall,
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    assert len(overall_calls) == 1
    call_kwargs = overall_calls[0]
    assert "category_sections" in call_kwargs
    assert isinstance(call_kwargs["category_sections"], dict)
    assert category.name in call_kwargs["category_sections"]


def _make_two_category_assessment():
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
def test_second_run_overall_assembled_from_all_categories_including_prior_runs(
    monkeypatch,
):
    call_count = [0]

    def category_stub(**kwargs):
        call_count[0] += 1
        return f"cat-content-{call_count[0]}"

    overall_calls = []

    def overall_stub(**kwargs):
        overall_calls.append(kwargs)
        return "overall"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        category_stub,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        overall_stub,
    )

    assessment, cat_a, cat_b = _make_two_category_assessment()

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)
    analysis1.status = Analysis.Status.COMPLETE
    analysis1.save(update_fields=["status"])

    cat_b_section = ReportSection.objects.get(analysis=analysis1, category=cat_b)

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
    assert sections_passed[cat_b.name] == cat_b_section.content


@pytest.mark.django_db
def test_task_creates_one_report_section_per_category_plus_overall(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: "Generated narrative",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "Generated narrative",
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=3, weight=Decimal("2.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    sections = ReportSection.objects.filter(analysis=analysis)
    expected = 2  # one for the category + one overall
    assert sections.count() == expected
    assert sections.filter(category=category).exists()
    assert sections.filter(category__isnull=True).exists()


@pytest.mark.django_db
def test_task_creates_separate_sections_for_two_categories(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        lambda **kwargs: "Generated narrative",
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "Generated narrative",
    )

    cat_a = CategoryFactory()
    cat_b = CategoryFactory()
    assessment = AssessmentFactory()

    for cat in (cat_a, cat_b):
        q = QuestionFactory(category=cat)
        opt = QuestionOptionFactory(question=q, rank=2, weight=Decimal("1.0000"))
        AnswerFactory(assessment=assessment, question=q, selected_option=opt)

    analysis = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis.pk)

    sections = ReportSection.objects.filter(analysis=analysis)
    expected = 3  # cat_a + cat_b + overall
    assert sections.count() == expected
    assert sections.filter(category=cat_a).exists()
    assert sections.filter(category=cat_b).exists()
    assert sections.filter(category__isnull=True).exists()


@pytest.mark.django_db
def test_report_sections_are_never_updated_after_creation(monkeypatch):
    call_count = 0

    def counting_client(**kwargs):
        nonlocal call_count
        call_count += 1
        return f"Run {call_count}"

    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_category_section",
        counting_client,
    )
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_overall_section",
        lambda **kwargs: "overall",
    )

    category = CategoryFactory()
    question = QuestionFactory(category=category)
    option = QuestionOptionFactory(question=question, rank=1, weight=Decimal("1.0000"))
    assessment = AssessmentFactory()
    AnswerFactory(assessment=assessment, question=question, selected_option=option)

    analysis1 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis1.pk)

    first_content = ReportSection.objects.get(
        analysis=analysis1,
        category=category,
    ).content

    analysis2 = Analysis.objects.create(assessment=assessment)
    run_analysis(analysis2.pk)

    # Original section is unchanged
    assert (
        ReportSection.objects.get(analysis=analysis1, category=category).content
        == first_content
    )
    # New analysis has its own new sections
    expected_new = 2  # one category + one overall
    assert ReportSection.objects.filter(analysis=analysis2).count() == expected_new
