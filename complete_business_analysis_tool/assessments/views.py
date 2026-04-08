"""Views for the assessments application."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView, ListView

from complete_business_analysis_tool.clients.forms import ClientForm

from .forms import AssessmentEntryForm
from .models import AssessmentTemplate


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
        return redirect("assessments:list")

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below and resubmit.",
        )
        return super().form_invalid(form)
