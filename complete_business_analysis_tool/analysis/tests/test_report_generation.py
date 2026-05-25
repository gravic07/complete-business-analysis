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
from complete_business_analysis_tool.reports.models import ReportSection


@pytest.mark.django_db
def test_task_creates_one_report_section_per_category_plus_overall(monkeypatch):
    monkeypatch.setattr(
        "complete_business_analysis_tool.analysis.tasks.generate_section",
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
        "complete_business_analysis_tool.analysis.tasks.generate_section",
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
        "complete_business_analysis_tool.analysis.tasks.generate_section",
        counting_client,
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
