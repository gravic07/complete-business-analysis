import json
from json import dumps as json_dumps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, FormView

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.analysis.services import (
    analysis_progress_message,
    start_analysis,
)
from complete_business_analysis_tool.analysis.tasks import run_analysis
from complete_business_analysis_tool.assessments.models import Assessment, Category
from complete_business_analysis_tool.reports.forms import FeedbackForm
from complete_business_analysis_tool.reports.models import (
    CategoryFeedback,
    Feedback,
    PDFExport,
)
from complete_business_analysis_tool.reports.queries import (
    latest_category_recommendations,
    latest_category_scores,
    latest_category_sections,
    latest_executive_summary,
    latest_recommendations_overview,
    latest_roadmap,
)
from complete_business_analysis_tool.reports.tasks import generate_pdf_export
from complete_business_analysis_tool.reports.utils.toc_calculator import (
    calculate_toc_page_numbers,
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
        context["has_complete_analysis"] = assessment.analyses.filter(
            status=Analysis.Status.COMPLETE,
        ).exists()
        context["latest_complete_pdf_export"] = (
            assessment.pdf_exports.filter(status=PDFExport.Status.COMPLETE)
            .order_by("-created_at")
            .first()
        )
        context["latest_analysis"] = assessment.analyses.order_by("-created_at").first()
        context["autostart"] = self.request.GET.get("autostart") == "1"
        context["autostart_feedback_id"] = self.request.GET.get("feedback_id", "")
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
        url = self.get_success_url()
        return redirect(f"{url}?autostart=1&feedback_id={feedback.pk}")


class UpdateAssessmentNameView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)
        name = request.POST.get("name", "").strip()
        if not name:
            return render(
                request,
                "snippets/reports/assessment-name.html",
                {"assessment": assessment, "error": "Report name is required."},
                status=422,
            )
        assessment.name = name
        assessment.save(update_fields=["name"])
        response = render(
            request,
            "snippets/reports/assessment-name.html",
            {"assessment": assessment},
        )
        response["HX-Trigger"] = json_dumps({"showToast": "Report name saved."})
        return response


class PDFTemplateView(DetailView):
    model = Assessment
    template_name = "pages/reports/report-pdf.html"
    context_object_name = "assessment"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        token = request.GET.get("token", "")
        try:
            value = TimestampSigner().unsign(token, max_age=60)
        except BadSignature, SignatureExpired:
            return HttpResponseForbidden()

        if str(value) != str(kwargs.get("pk", "")):
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object
        sections = latest_category_sections(assessment)
        category_names = [s.category.name for s in sections]
        context["executive_summary"] = latest_executive_summary(assessment)
        context["category_sections"] = _merge_sections_and_recs(
            sections,
            latest_category_recommendations(assessment),
        )
        context["recommendations_overview"] = latest_recommendations_overview(assessment)
        context["roadmap"] = latest_roadmap(assessment)
        context["roadmap_overview"] = _ROADMAP_OVERVIEW
        context["chart_data"] = _build_chart_data(assessment)
        scores = latest_category_scores(assessment)
        context["category_scores"] = scores
        context["cba_total_score"] = _compute_cba_total(scores)
        context["toc_page_numbers"] = calculate_toc_page_numbers(
            category_names,
            assessment.name,
        )
        return context


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


def _compute_cba_total(scores) -> int | None:
    if not scores:
        return None
    total = sum(s.score for s in scores)
    max_total = sum(s.max_possible_score for s in scores if s.max_possible_score)
    if not max_total:
        return None
    return round(float(total / max_total * 100))


class TriggerPDFExportView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)
        export = PDFExport.objects.create(assessment=assessment)
        generate_pdf_export.delay(str(export.pk))
        return JsonResponse({"pdf_export_id": str(export.pk)})


class PDFExportStatusView(LoginRequiredMixin, View):
    def get(self, request, pk):
        export = get_object_or_404(PDFExport, pk=pk)
        download_url = export.file.url if export.file else ""
        return JsonResponse({"status": export.status, "download_url": download_url})


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class TriggerAnalysisView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)

        retry_analysis_id = request.POST.get("retry_analysis_id")
        if retry_analysis_id:
            analysis = get_object_or_404(
                Analysis,
                pk=retry_analysis_id,
                assessment=assessment,
            )
            updated = Analysis.objects.filter(
                pk=analysis.pk,
                status=Analysis.Status.FAILED,
            ).update(status=Analysis.Status.PENDING)
            if updated:
                run_analysis.delay(str(analysis.pk))
            analysis.refresh_from_db()
            return JsonResponse(
                {"analysis_id": str(analysis.pk), "status": analysis.status},
            )

        feedback = None
        feedback_id = request.POST.get("feedback_id")
        if feedback_id:
            feedback = get_object_or_404(Feedback, pk=feedback_id, assessment=assessment)
        try:
            analysis = start_analysis(assessment, feedback=feedback)
        except ValidationError:
            analysis = assessment.analyses.order_by("-created_at").first()
        return JsonResponse({"analysis_id": str(analysis.pk), "status": analysis.status})


class AnalysisStatusView(LoginRequiredMixin, View):
    def get(self, request, pk):
        analysis = get_object_or_404(Analysis, pk=pk)
        data = {"status": analysis.status}
        if analysis.status in (Analysis.Status.PENDING, Analysis.Status.PROCESSING):
            data["message"] = analysis_progress_message(analysis)
        return JsonResponse(data)
