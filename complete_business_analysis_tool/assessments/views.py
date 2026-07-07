"""Views for the assessments application."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView

from complete_business_analysis_tool.clients.forms import ClientForm

from .forms import AssessmentEntryForm
from .models import Assessment, AssessmentTemplate


class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "pages/assessments/assessment-detail.html"
    context_object_name = "assessment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answers = self.object.answers.select_related("question__category").order_by(
            "question__category__name",
            "created_at",
        )
        groups: dict[str, list] = {}
        for answer in answers:
            cat = (
                answer.question.category
                if answer.question and answer.question.category
                else None
            )
            cat_name = cat.name if cat else "General"
            groups.setdefault(cat_name, []).append(answer)
        context["grouped_answers"] = list(groups.items())
        context["analyses"] = self.object.analyses.order_by("-created_at")
        return context


class AssessmentTemplateListView(LoginRequiredMixin, ListView):
    model = AssessmentTemplate
    template_name = "pages/assessments/assessment-list.html"
    context_object_name = "templates"
    ordering = ["title"]


class AssessmentEntryView(LoginRequiredMixin, FormView):
    template_name = "pages/assessments/assessment-entry.html"
    form_class = AssessmentEntryForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.assessment_template = get_object_or_404(
            AssessmentTemplate,
            pk=kwargs["pk"],
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["template"] = self.assessment_template
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get("client")
        if client_id:
            initial["client"] = client_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment_template"] = self.assessment_template
        context["client_form"] = ClientForm()
        return context

    def form_valid(self, form):
        assessment = form.save()
        messages.success(
            self.request,
            f"Assessment for {assessment.client} completed successfully.",
        )
        url = reverse("reports:report", kwargs={"pk": assessment.pk})
        return redirect(f"{url}?autostart=1")

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below and resubmit.",
        )
        return super().form_invalid(form)
