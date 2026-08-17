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
from complete_business_analysis_tool.reports.models import CategoryRecommendations
from complete_business_analysis_tool.reports.queries import (
    latest_category_recommendations,
)


def _make_assessment_with_two_categories():
    cat_a = CategoryFactory.create(name="Alpha")
    cat_b = CategoryFactory.create(name="Beta")
    assessment = AssessmentFactory.create()
    for cat in (cat_a, cat_b):
        q = QuestionFactory.create(category=cat)
        opt = QuestionOptionFactory.create(question=q, rank=1, weight=Decimal("1.0000"))
        AnswerFactory.create(assessment=assessment, question=q, selected_option=opt)
    return assessment, cat_a, cat_b


def _recs():
    return ["r1", "r2", "r3", "r4", "r5", "r6", "r7"]


@pytest.mark.django_db
def test_latest_category_recommendations_returns_one_per_category():
    assessment, cat_a, cat_b = _make_assessment_with_two_categories()
    analysis = Analysis.objects.create(assessment=assessment)
    CategoryRecommendations.objects.create(
        analysis=analysis,
        category=cat_a,
        recommendations=_recs(),
    )
    CategoryRecommendations.objects.create(
        analysis=analysis,
        category=cat_b,
        recommendations=_recs(),
    )

    result = latest_category_recommendations(assessment)

    expected_result_cnt = 2
    assert len(result) == expected_result_cnt
    names = [r.category.name for r in result]
    assert names == ["Alpha", "Beta"]


@pytest.mark.django_db
def test_latest_category_recommendations_returns_most_recent_per_category():
    assessment, cat_a, cat_b = _make_assessment_with_two_categories()
    analysis1 = Analysis.objects.create(assessment=assessment)
    analysis2 = Analysis.objects.create(assessment=assessment)

    old_recs = ["old"] * 7
    new_recs = ["new"] * 7

    CategoryRecommendations.objects.create(
        analysis=analysis1,
        category=cat_a,
        recommendations=old_recs,
    )
    CategoryRecommendations.objects.create(
        analysis=analysis2,
        category=cat_a,
        recommendations=new_recs,
    )
    CategoryRecommendations.objects.create(
        analysis=analysis1,
        category=cat_b,
        recommendations=old_recs,
    )

    result = latest_category_recommendations(assessment)

    by_name = {r.category.name: r for r in result}
    assert by_name["Alpha"].recommendations == new_recs
    assert by_name["Beta"].recommendations == old_recs


@pytest.mark.django_db
def test_latest_category_recommendations_ordered_by_name():
    cat_z = CategoryFactory.create(name="Zeta")
    cat_a = CategoryFactory.create(name="Alpha")
    assessment = AssessmentFactory.create()
    for cat in (cat_z, cat_a):
        q = QuestionFactory.create(category=cat)
        opt = QuestionOptionFactory.create(question=q, rank=1, weight=Decimal("1.0000"))
        AnswerFactory.create(assessment=assessment, question=q, selected_option=opt)
    analysis = Analysis.objects.create(assessment=assessment)
    CategoryRecommendations.objects.create(
        analysis=analysis,
        category=cat_z,
        recommendations=_recs(),
    )
    CategoryRecommendations.objects.create(
        analysis=analysis,
        category=cat_a,
        recommendations=_recs(),
    )

    result = latest_category_recommendations(assessment)

    assert [r.category.name for r in result] == ["Alpha", "Zeta"]


@pytest.mark.django_db
def test_latest_category_recommendations_returns_empty_when_none_exist():
    assessment = AssessmentFactory.create()
    assert latest_category_recommendations(assessment) == []
