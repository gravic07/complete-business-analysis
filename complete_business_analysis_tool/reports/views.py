from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Subquery
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
    ReportSection,
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
        context["sections"] = _assemble_report(assessment)
        context["feedback_form"] = form
        context["category_fields"] = [
            (cat, form[f"category_{cat.pk}"]) for cat in categories
        ]
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
        context["sections"] = _assemble_report(self.assessment)
        context["feedback_form"] = form
        context["category_fields"] = [
            (cat, form[f"category_{cat.pk}"]) for cat in self.categories
        ]
        return context

    def get_success_url(self):
        return reverse("reports:report", kwargs={"pk": self.assessment.pk})

    def form_valid(self, form):
        overall_text = (form.cleaned_data.get("overall_text") or "").strip() or None
        feedback = Feedback.objects.create(
            assessment=self.assessment,
            overall_text=overall_text,
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


def _assessment_categories(assessment: Assessment):
    return (
        Category.objects.filter(questions__answers__assessment=assessment)
        .distinct()
        .order_by("name")
    )


def _assemble_report(assessment: Assessment) -> list[ReportSection]:
    """Return the latest ReportSection per category across all Analysis runs.

    Overall section (category=None) is first, then categories ordered by name.
    """

    sections = list(
        ReportSection.objects.filter(
            pk__in=Subquery(
                ReportSection.objects.filter(analysis__assessment=assessment)
                .order_by("category_id", "-analysis__created_at")
                .distinct("category_id")
                .values("pk"),
            ),
        )
        .select_related("category")
        .order_by("category__name"),
    )

    overall = [s for s in sections if s.category is None]
    categorised = [s for s in sections if s.category is not None]
    return overall + categorised
