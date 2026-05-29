from decimal import Decimal

import pytest

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import (
    AnswerFactory,
    AssessmentFactory,
    CategoryFactory,
    QuestionFactory,
    QuestionOptionFactory,
)
from complete_business_analysis_tool.reports.models import (
    CategorySection,
    ExecutiveSummary,
    RecommendationsOverview,
    Roadmap,
)
from complete_business_analysis_tool.reports.queries import (
    latest_category_sections,
    latest_executive_summary,
    latest_recommendations_overview,
    latest_roadmap,
)


def _make_assessment_with_two_categories():
    cat_a = CategoryFactory(name="Alpha")
    cat_b = CategoryFactory(name="Beta")
    assessment = AssessmentFactory()
    for cat in (cat_a, cat_b):
        q = QuestionFactory(category=cat)
        opt = QuestionOptionFactory(question=q, rank=1, weight=Decimal("1.0000"))
        AnswerFactory(assessment=assessment, question=q, selected_option=opt)
    return assessment, cat_a, cat_b


@pytest.mark.django_db
def test_latest_category_sections_returns_one_section_per_category():
    assessment, cat_a, cat_b = _make_assessment_with_two_categories()
    analysis = Analysis.objects.create(assessment=assessment)
    CategorySection.objects.create(
        analysis=analysis,
        category=cat_a,
        overview="a1",
        impact="",
        path_forward="",
    )
    CategorySection.objects.create(
        analysis=analysis,
        category=cat_b,
        overview="b1",
        impact="",
        path_forward="",
    )

    sections = latest_category_sections(assessment)
    expected_sections_cnt = 2
    assert len(sections) == expected_sections_cnt
    names = [s.category.name for s in sections]
    assert names == ["Alpha", "Beta"]


@pytest.mark.django_db
def test_latest_category_sections_returns_most_recent_per_category():
    assessment, cat_a, cat_b = _make_assessment_with_two_categories()
    analysis1 = Analysis.objects.create(assessment=assessment)
    analysis2 = Analysis.objects.create(assessment=assessment)
    CategorySection.objects.create(
        analysis=analysis1,
        category=cat_a,
        overview="a-old",
        impact="",
        path_forward="",
    )
    CategorySection.objects.create(
        analysis=analysis2,
        category=cat_a,
        overview="a-new",
        impact="",
        path_forward="",
    )
    CategorySection.objects.create(
        analysis=analysis1,
        category=cat_b,
        overview="b-only",
        impact="",
        path_forward="",
    )

    sections = latest_category_sections(assessment)

    by_name = {s.category.name: s for s in sections}
    assert by_name["Alpha"].overview == "a-new"
    assert by_name["Beta"].overview == "b-only"


@pytest.mark.django_db
def test_latest_category_sections_ordered_by_name():
    cat_z = CategoryFactory(name="Zeta")
    cat_a = CategoryFactory(name="Alpha")
    assessment = AssessmentFactory()
    for cat in (cat_z, cat_a):
        q = QuestionFactory(category=cat)
        opt = QuestionOptionFactory(question=q, rank=1, weight=Decimal("1.0000"))
        AnswerFactory(assessment=assessment, question=q, selected_option=opt)
    analysis = Analysis.objects.create(assessment=assessment)
    CategorySection.objects.create(
        analysis=analysis,
        category=cat_z,
        overview="z",
        impact="",
        path_forward="",
    )
    CategorySection.objects.create(
        analysis=analysis,
        category=cat_a,
        overview="a",
        impact="",
        path_forward="",
    )

    sections = latest_category_sections(assessment)

    assert [s.category.name for s in sections] == ["Alpha", "Zeta"]


@pytest.mark.django_db
def test_latest_executive_summary_returns_none_when_none_exist():
    assessment = AssessmentFactory()

    result = latest_executive_summary(assessment)

    assert result is None


@pytest.mark.django_db
def test_latest_executive_summary_returns_most_recent():
    assessment = AssessmentFactory()
    analysis1 = Analysis.objects.create(assessment=assessment)
    analysis2 = Analysis.objects.create(assessment=assessment)
    ExecutiveSummary.objects.create(analysis=analysis1, content="first")
    ExecutiveSummary.objects.create(analysis=analysis2, content="second")

    result = latest_executive_summary(assessment)

    assert result is not None
    assert result.content == "second"


@pytest.mark.django_db
def test_latest_recommendations_overview_returns_none_when_none_exist():
    assessment = AssessmentFactory()

    result = latest_recommendations_overview(assessment)

    assert result is None


@pytest.mark.django_db
def test_latest_recommendations_overview_returns_most_recent():
    assessment = AssessmentFactory()
    analysis1 = Analysis.objects.create(assessment=assessment)
    analysis2 = Analysis.objects.create(assessment=assessment)
    RecommendationsOverview.objects.create(analysis=analysis1, content="first overview")
    RecommendationsOverview.objects.create(analysis=analysis2, content="second overview")

    result = latest_recommendations_overview(assessment)

    assert result is not None
    assert result.content == "second overview"


@pytest.mark.django_db
def test_latest_roadmap_returns_none_when_none_exist():
    assessment = AssessmentFactory()

    result = latest_roadmap(assessment)

    assert result is None


@pytest.mark.django_db
def test_latest_roadmap_returns_most_recent():
    assessment = AssessmentFactory()
    analysis1 = Analysis.objects.create(assessment=assessment)
    analysis2 = Analysis.objects.create(assessment=assessment)
    Roadmap.objects.create(
        analysis=analysis1,
        months=[],
        potential_challenges="first",
        post_implementation_outcomes="",
        closing_reflections="",
    )
    Roadmap.objects.create(
        analysis=analysis2,
        months=[],
        potential_challenges="second",
        post_implementation_outcomes="",
        closing_reflections="",
    )

    result = latest_roadmap(assessment)

    assert result is not None
    assert result.potential_challenges == "second"
