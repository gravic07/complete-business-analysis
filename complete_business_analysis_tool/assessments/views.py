"""Views for the assessments application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from .forms import AssessmentAnswerForm, AssessmentStartForm, CategoryGuidanceForm
from .models import Assessment, AssessmentTemplate, Category, CategoryGuidance
from .services import assessment_completion_status

if TYPE_CHECKING:
    import uuid


class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "pages/assessments/assessment-detail.html"
    context_object_name = "assessment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object

        if assessment.status != Assessment.Status.COMPLETE:
            context["completion_status"] = assessment_completion_status(assessment)
            return context

        answers = assessment.answers.select_related("question__category").order_by(
            "question__category__name",
            "created_at",
        )
        guidance_by_category = dict(
            CategoryGuidance.objects.filter(assessment=assessment).values_list(
                "category_id",
                "text",
            ),
        )
        groups: dict[uuid.UUID | None, dict] = {}
        for answer in answers:
            cat = (
                answer.question.category
                if answer.question and answer.question.category
                else None
            )
            key: uuid.UUID | None = cat.pk if cat else None
            if key not in groups:
                groups[key] = {
                    "name": cat.name if cat else "General",
                    "answers": [],
                    "guidance": guidance_by_category.get(key) if key else None,
                }
            groups[key]["answers"].append(answer)
        context["grouped_answers"] = list(groups.values())
        context["analyses"] = assessment.analyses.order_by("-created_at")
        return context


class AssessmentTemplateListView(LoginRequiredMixin, ListView):
    model = AssessmentTemplate
    template_name = "pages/assessments/assessment-list.html"
    context_object_name = "templates"
    ordering = ["title"]


class AssessmentStartView(LoginRequiredMixin, FormView):
    template_name = "pages/assessments/assessment-start.html"
    form_class = AssessmentStartForm

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
        return context

    def form_valid(self, form):
        assessment = form.save()
        return redirect("assessments:detail", pk=assessment.pk)


class AssessmentAnswerView(LoginRequiredMixin, FormView):
    template_name = "pages/assessments/assessment-answer.html"
    form_class = AssessmentAnswerForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.assessment = get_object_or_404(Assessment, pk=kwargs["pk"])

    def _reject_if_complete(self):
        """Block access once the assessment is locked.

        Called from get()/post() rather than dispatch() so that
        LoginRequiredMixin's auth check (enforced in dispatch()) always runs
        first, regardless of assessment status.
        """
        if self.assessment.status == Assessment.Status.COMPLETE:
            messages.error(
                self.request,
                "This assessment is already complete; answers can no longer be edited.",
            )
            return redirect("assessments:detail", pk=self.assessment.pk)
        return None

    def get(self, request, *args, **kwargs):
        return self._reject_if_complete() or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._reject_if_complete() or super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["assessment"] = self.assessment
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        existing_answers = self.assessment.answers.select_related("question")
        for answer in existing_answers:
            if answer.question and answer.selected_option_id:
                initial[f"question_{answer.question.pk.hex}"] = str(
                    answer.selected_option_id,
                )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment"] = self.assessment
        return context

    def get_success_url(self):
        return reverse("assessments:detail", kwargs={"pk": self.assessment.pk})

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Answers saved.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Please correct the errors below and resubmit.",
        )
        return super().form_invalid(form)


class CategoryGuidanceView(LoginRequiredMixin, FormView):
    template_name = "pages/assessments/assessment-guidance.html"
    form_class = CategoryGuidanceForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.assessment = get_object_or_404(Assessment, pk=kwargs["pk"])
        self.categories = (
            Category.objects.filter(
                questions__template_questions__template=self.assessment.template,
            )
            .distinct()
            .order_by("name")
        )

    def _reject_if_complete(self):
        """Block access once the assessment is locked.

        Called from get()/post() rather than dispatch() so that
        LoginRequiredMixin's auth check (enforced in dispatch()) always runs
        first, regardless of assessment status.
        """
        if self.assessment.status == Assessment.Status.COMPLETE:
            messages.error(
                self.request,
                "This assessment is already complete; guidance can no longer be edited.",
            )
            return redirect("assessments:detail", pk=self.assessment.pk)
        return None

    def get(self, request, *args, **kwargs):
        return self._reject_if_complete() or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._reject_if_complete() or super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["categories"] = self.categories
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        existing_text = dict(
            CategoryGuidance.objects.filter(assessment=self.assessment).values_list(
                "category_id",
                "text",
            ),
        )
        for category in self.categories:
            text = existing_text.get(category.pk)
            if text:
                initial[f"category_{category.pk.hex}"] = text
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessment"] = self.assessment
        return context

    def get_success_url(self):
        return reverse("assessments:detail", kwargs={"pk": self.assessment.pk})

    @transaction.atomic
    def form_valid(self, form):
        for category in self.categories:
            text = (form.cleaned_data.get(f"category_{category.pk.hex}") or "").strip()
            if text:
                CategoryGuidance.objects.update_or_create(
                    assessment=self.assessment,
                    category=category,
                    defaults={"text": text},
                )
            else:
                CategoryGuidance.objects.filter(
                    assessment=self.assessment,
                    category=category,
                ).delete()

        self.assessment.guidance_submitted_at = timezone.now()
        update_fields = ["guidance_submitted_at"]
        if self.assessment.status == Assessment.Status.DRAFT:
            self.assessment.status = Assessment.Status.IN_PROGRESS
            update_fields.append("status")
        self.assessment.save(update_fields=update_fields)

        messages.success(self.request, "Guidance saved.")
        return super().form_valid(form)


class MarkCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk)

        if assessment.status == Assessment.Status.COMPLETE:
            return redirect("reports:report", pk=assessment.pk)

        status = assessment_completion_status(assessment)

        if not status.eligible:
            messages.error(
                request,
                "Cannot mark this assessment complete: " + " ".join(status.reasons),
            )
            return redirect("assessments:detail", pk=assessment.pk)

        assessment.status = Assessment.Status.COMPLETE
        assessment.save(update_fields=["status"])

        url = reverse("reports:report", kwargs={"pk": assessment.pk})
        return redirect(f"{url}?autostart=1")
