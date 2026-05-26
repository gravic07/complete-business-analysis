from celery import shared_task
from django.db.models import Max

from complete_business_analysis_tool.analysis.models import Analysis, CategoryScore
from complete_business_analysis_tool.analysis.scope import resolve_scope
from complete_business_analysis_tool.analysis.scoring import compute_scores
from complete_business_analysis_tool.assessments.models import Category
from complete_business_analysis_tool.reports.ai_service import (
    generate_category_section,
    generate_executive_summary,
)
from complete_business_analysis_tool.reports.models import (
    CategorySection,
    ExecutiveSummary,
)
from complete_business_analysis_tool.reports.queries import latest_sections_by_category


def _build_answer_dicts(assessment) -> list[dict]:
    answers = (
        assessment.answers.select_related(
            "selected_option__question__category",
        )
        .annotate(max_rank=Max("question__options__rank"))
        .filter(selected_option__isnull=False)
    )
    return [
        {
            "category_id": str(a.selected_option.question.category_id),
            "category_name": a.selected_option.question.category.name,
            "rank": a.selected_option.rank,
            "weight": a.selected_option.weight,
            "max_rank": a.max_rank,
            "question_snapshot": a.question_snapshot,
            "option_snapshot": a.option_snapshot,
        }
        for a in answers
        if a.selected_option.question.category_id is not None
    ]


def _run_analysis_work(analysis: Analysis) -> None:

    answer_dicts = _build_answer_dicts(analysis.assessment)
    result = compute_scores(answer_dicts)
    all_category_ids = set(result.category_scores.keys())

    # Determine scope and collect feedback context
    if analysis.feedback_id:
        feedback = analysis.feedback
        cf_qs = list(feedback.category_feedbacks.all())
        category_feedback_ids = {str(cf.category_id) for cf in cf_qs}
        category_feedback_by_id = {str(cf.category_id): cf.text for cf in cf_qs}
        overall_feedback = feedback.report_feedback
        in_scope_ids = resolve_scope(
            overall_text=overall_feedback,
            category_feedback_ids=category_feedback_ids,
            all_category_ids=all_category_ids,
        )
    else:
        overall_feedback = None
        category_feedback_by_id = {}
        in_scope_ids = all_category_ids

    existing_score_cat_ids = {
        str(pk)
        for pk in CategoryScore.objects.filter(analysis=analysis).values_list(
            "category_id",
            flat=True,
        )
    }
    CategoryScore.objects.bulk_create(
        [
            CategoryScore(
                analysis=analysis,
                category_id=cat_id,
                score=score,
                max_possible_score=result.category_max_scores[cat_id],
            )
            for cat_id, score in result.category_scores.items()
            if cat_id in in_scope_ids and cat_id not in existing_score_cat_ids
        ],
    )

    analysis.total_score = result.total
    analysis.save(update_fields=["total_score"])

    answers_by_category: dict[str, list[dict]] = {}
    category_names: dict[str, str] = {}
    for a in answer_dicts:
        cat_id = a["category_id"]
        answers_by_category.setdefault(cat_id, []).append(a)
        category_names[cat_id] = a["category_name"]

    category_score_by_name = {
        category_names[cat_id]: score for cat_id, score in result.category_scores.items()
    }

    categories = Category.objects.filter(pk__in=in_scope_ids)
    for category in categories:
        cat_id = str(category.pk)

        if CategorySection.objects.filter(analysis=analysis, category=category).exists():
            continue

        prior_section = (
            CategorySection.objects.filter(
                analysis__assessment=analysis.assessment,
                category=category,
            )
            .order_by("-analysis__created_at")
            .first()
        )

        feedback_parts = [
            t for t in [overall_feedback, category_feedback_by_id.get(cat_id)] if t
        ]
        combined_feedback = "\n\n".join(feedback_parts) or None

        content = generate_category_section(
            answers=answers_by_category.get(cat_id, []),
            feedback_text=combined_feedback,
            prior_overview=prior_section.overview if prior_section else None,
            prior_impact=prior_section.impact if prior_section else None,
            prior_path_forward=prior_section.path_forward if prior_section else None,
        )
        CategorySection.objects.create(
            analysis=analysis,
            category=category,
            overview=content["overview"],
            impact=content["impact"],
            path_forward=content["path_forward"],
        )

    all_current_sections = latest_sections_by_category(analysis.assessment)
    category_sections_dict = {s.category.name: s.overview for s in all_current_sections}
    category_max_scores_by_name = {
        category_names[cat_id]: result.category_max_scores[cat_id]
        for cat_id in result.category_scores
    }
    prior_overall = (
        ExecutiveSummary.objects.filter(
            analysis__assessment=analysis.assessment,
        )
        .order_by("-analysis__created_at")
        .first()
    )
    if not ExecutiveSummary.objects.filter(analysis=analysis).exists():
        overall_content = generate_executive_summary(
            category_sections=category_sections_dict,
            category_scores=category_score_by_name,
            category_max_scores=category_max_scores_by_name,
            prior_content=prior_overall.content if prior_overall else None,
            feedback_text=overall_feedback,
        )
        ExecutiveSummary.objects.create(
            analysis=analysis,
            content=overall_content,
        )


@shared_task()
def run_analysis(analysis_pk: str) -> None:
    analysis = Analysis.objects.get(pk=analysis_pk)
    analysis.status = Analysis.Status.PROCESSING
    analysis.save(update_fields=["status"])

    try:
        _run_analysis_work(analysis)
    except Exception:  # noqa: BLE001
        analysis.status = Analysis.Status.FAILED
        analysis.save(update_fields=["status"])
        return

    analysis.status = Analysis.Status.COMPLETE
    analysis.save(update_fields=["status"])
