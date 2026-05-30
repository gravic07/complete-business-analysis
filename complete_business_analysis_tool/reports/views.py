import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, FormView

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.models import Assessment, Category
from complete_business_analysis_tool.reports.forms import FeedbackForm
from complete_business_analysis_tool.reports.models import (
    CategoryFeedback,
    Feedback,
)
from complete_business_analysis_tool.reports.queries import (
    latest_category_recommendations,
    latest_category_scores,
    latest_category_sections,
    latest_executive_summary,
    latest_recommendations_overview,
    latest_roadmap,
)

_ROADMAP_OVERVIEW = (
    "This 12-month roadmap is designed to guide your business through a structured "
    "implementation of the key improvements identified in the assessment and "
    "recommendations. The plan focuses on actionable, prioritized goals that address the "
    "most critical areas of opportunity — including strategy, people, processes, "
    "personal development, and technology adoption.\n\n"
    "Each month contains clear goals and specific action items, enabling the business to "
    "track progress effectively and build sustainable momentum. The roadmap encourages "
    "selecting at least five foundational recommendations to pursue initially, ensuring "
    "improvements are manageable and measurable. These selections emphasize establishing "
    "disciplined strategic routines, enhancing team recruitment and development, "
    "streamlining operational processes, strengthening leadership capabilities, and "
    "modernizing systems where appropriate.\n\n"
    "Potential challenges such as resistance to change, limited resources, time "
    "constraints, and the need for new skills are acknowledged throughout, with the "
    "roadmap designed to mitigate these through incremental steps and clear milestones. "
    "By following this plan, the business can transform reactive management into "
    "proactive leadership, foster a capable and engaged workforce, optimize operations "
    "for efficiency, and leverage technology for competitive advantage."
)


class ReportView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "pages/reports/report-detail.html"
    context_object_name = "assessment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object
        categories = _assessment_categories(assessment)
        form = FeedbackForm(categories=categories)
        context["executive_summary"] = latest_executive_summary(assessment)
        context["category_sections"] = _merge_sections_and_recs(
            latest_category_sections(assessment),
            latest_category_recommendations(assessment),
        )
        context["recommendations_overview"] = latest_recommendations_overview(assessment)
        context["roadmap"] = latest_roadmap(assessment)
        context["roadmap_overview"] = _ROADMAP_OVERVIEW
        context["chart_data"] = _build_chart_data(assessment)
        context["feedback_form"] = form
        category_field_map = {cat.pk: form[f"category_{cat.pk}"] for cat in categories}
        for section in context["category_sections"]:
            section["feedback_field"] = category_field_map.get(section["category"].pk)
        return context


class SubmitFeedbackView(LoginRequiredMixin, FormView):
    form_class = FeedbackForm
    template_name = "pages/reports/report-detail.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.assessment = get_object_or_404(Assessment, pk=kwargs["pk"])
        self.categories = _assessment_categories(self.assessment)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.categories
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["assessment"] = self.assessment
        context["executive_summary"] = latest_executive_summary(self.assessment)
        context["category_sections"] = _merge_sections_and_recs(
            latest_category_sections(self.assessment),
            latest_category_recommendations(self.assessment),
        )
        context["recommendations_overview"] = latest_recommendations_overview(
            self.assessment,
        )
        context["chart_data"] = _build_chart_data(self.assessment)
        context["feedback_form"] = form
        category_field_map = {
            cat.pk: form[f"category_{cat.pk}"] for cat in self.categories
        }
        for section in context["category_sections"]:
            section["feedback_field"] = category_field_map.get(section["category"].pk)
        return context

    def get_success_url(self):
        return reverse("reports:report", kwargs={"pk": self.assessment.pk})

    def form_valid(self, form):
        report_feedback = (form.cleaned_data.get("report_feedback") or "").strip()
        feedback = Feedback.objects.create(
            assessment=self.assessment,
            report_feedback=report_feedback,
        )
        for category in self.categories:
            text = (form.cleaned_data.get(f"category_{category.pk}") or "").strip()
            if text:
                CategoryFeedback.objects.create(
                    feedback=feedback,
                    category=category,
                    text=text,
                )
        analysis = Analysis(assessment=self.assessment, feedback=feedback)
        try:
            analysis.full_clean()
        except ValidationError as e:
            feedback.delete()
            form.add_error(None, e)
            return self.form_invalid(form)
        analysis.save()
        run_analysis.delay(str(analysis.pk))
        return super().form_valid(form)


def _build_chart_data(assessment) -> str | None:
    scores = latest_category_scores(assessment)
    if not scores:
        return None
    data = sorted(
        [
            {
                "category": s.category.name,
                "pct": round(float(s.score / s.max_possible_score * 100), 1)
                if s.max_possible_score
                else 0.0,
            }
            for s in scores
        ],
        key=lambda x: x["pct"],
        reverse=True,
    )
    return json.dumps(data)


def _merge_sections_and_recs(sections, recs):
    rec_by_cat = {r.category_id: r.recommendations for r in recs}
    return [
        {
            "category": s.category,
            "overview": s.overview,
            "impact": s.impact,
            "path_forward": s.path_forward,
            "recommendations": rec_by_cat.get(s.category_id, []),
        }
        for s in sections
    ]


def _assessment_categories(assessment: Assessment):
    return (
        Category.objects.filter(questions__answers__assessment=assessment)
        .distinct()
        .order_by("name")
    )
