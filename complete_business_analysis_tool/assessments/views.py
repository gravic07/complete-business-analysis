"""Views for the assessments application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from .forms import AssessmentAnswerForm, AssessmentStartForm, CategoryGuidanceForm
from .models import (
    Assessment,
    AssessmentTemplate,
    Category,
    CategoryGuidance,
    ClientAccessLink,
)
from .services import (
    assessment_completion_status,
    generate_client_access_link,
    regenerate_client_access_link,
    revoke_client_access_link,
)

if TYPE_CHECKING:
    import uuid


# The client_portal app that will own this route (PRD tickets 03-05) doesn't
# exist yet, so this can't be reverse()'d by name. Centralized here as the
# one place to update once that app's URLconf lands.
CLIENT_ACCESS_LINK_PATH_TEMPLATE = "/client-access/{token}/"


def _access_link_state(
    request: HttpRequest,
    assessment: Assessment,
    link_type: str,
    link: ClientAccessLink | None,
) -> dict:
    """Build the Generate/Copy/Revoke/Regenerate control state for one step.

    Takes the (assessment, link_type) row already fetched by the caller
    rather than querying for it, so a caller needing state for both steps
    (the detail hub) can fetch both rows in a single query.
    """
    context = {
        "link_type": link_type,
        "client_has_email": bool(assessment.client.email),
        "access_link": None,
        "access_link_url": None,
    }
    if (
        link is not None
        and link.status == ClientAccessLink.Status.ACTIVE
        and assessment.status != Assessment.Status.COMPLETE
    ):
        context["access_link"] = link
        context["access_link_url"] = request.build_absolute_uri(
            CLIENT_ACCESS_LINK_PATH_TEMPLATE.format(token=link.token),
        )
    return context


def _client_access_link_context(
    request: HttpRequest,
    assessment: Assessment,
    link_type: str,
) -> dict:
    """Look up the (assessment, link_type) row and build its control state.

    Convenience wrapper around _access_link_state() for the single-step
    Guidance/Answer pages, which only ever need one link type at a time.
    """
    link = ClientAccessLink.objects.filter(
        assessment=assessment,
        link_type=link_type,
    ).first()
    return _access_link_state(request, assessment, link_type, link)


class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = "pages/assessments/assessment-detail.html"
    context_object_name = "assessment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object

        if assessment.status != Assessment.Status.COMPLETE:
            context["completion_status"] = assessment_completion_status(assessment)
            links_by_type = {
                link.link_type: link
                for link in ClientAccessLink.objects.filter(assessment=assessment)
            }
            context["guidance_access"] = _access_link_state(
                self.request,
                assessment,
                ClientAccessLink.LinkType.GUIDANCE,
                links_by_type.get(ClientAccessLink.LinkType.GUIDANCE),
            )
            context["answer_access"] = _access_link_state(
                self.request,
                assessment,
                ClientAccessLink.LinkType.ANSWER,
                links_by_type.get(ClientAccessLink.LinkType.ANSWER),
            )
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
        context["has_guidance"] = bool(guidance_by_category)
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
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("client"),
            pk=kwargs["pk"],
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
        context["answer_access"] = _client_access_link_context(
            self.request,
            self.assessment,
            ClientAccessLink.LinkType.ANSWER,
        )
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
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("client"),
            pk=kwargs["pk"],
        )
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
        context["guidance_access"] = _client_access_link_context(
            self.request,
            self.assessment,
            ClientAccessLink.LinkType.GUIDANCE,
        )
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


class ClientAccessLinkActionView(LoginRequiredMixin, View):
    """Shared setup/redirect handling for Generate/Revoke/Regenerate endpoints.

    Each subclass implements post() for its own action.
    """

    http_method_names = ["post"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.assessment = get_object_or_404(
            Assessment.objects.select_related("client"),
            pk=kwargs["pk"],
        )
        link_type = kwargs["link_type"]
        if link_type not in ClientAccessLink.LinkType.values:
            raise Http404
        self.link_type = link_type

    def get_redirect_url(self):
        next_url = self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse("assessments:detail", kwargs={"pk": self.assessment.pk})

    def _reject_if_complete(self):
        """Block the action once the assessment is locked.

        A completed Assessment already implicitly invalidates both of its
        links (see is_client_access_link_valid); this guard additionally
        stops a direct POST from mutating a ClientAccessLink row that the
        UI no longer exposes controls for.
        """
        if self.assessment.status == Assessment.Status.COMPLETE:
            messages.error(
                self.request,
                "This assessment is already complete; its access links can no "
                "longer be changed.",
            )
            return redirect(self.get_redirect_url())
        return None

    def _get_active_link(self):
        """Fetch the currently-active link for (assessment, link_type).

        Revoke and Regenerate only ever act on an active link — the UI never
        offers them otherwise. Scoping the lookup to status=ACTIVE also stops
        a stale Regenerate request from reactivating an already-revoked link
        and bypassing Generate's Client-has-an-email check.
        """
        return get_object_or_404(
            ClientAccessLink,
            assessment=self.assessment,
            link_type=self.link_type,
            status=ClientAccessLink.Status.ACTIVE,
        )


class ClientAccessLinkGenerateView(ClientAccessLinkActionView):
    def post(self, request, *args, **kwargs):
        rejected = self._reject_if_complete()
        if rejected:
            return rejected

        if not self.assessment.client.email:
            messages.error(
                request,
                "Add an email address to this Client before generating an access link.",
            )
            return redirect(self.get_redirect_url())

        generate_client_access_link(self.assessment, self.link_type)
        messages.success(request, "Client access link generated.")
        return redirect(self.get_redirect_url())


class ClientAccessLinkRevokeView(ClientAccessLinkActionView):
    def post(self, request, *args, **kwargs):
        rejected = self._reject_if_complete()
        if rejected:
            return rejected

        link = self._get_active_link()
        revoke_client_access_link(link)
        messages.success(request, "Client access link revoked.")
        return redirect(self.get_redirect_url())


class ClientAccessLinkRegenerateView(ClientAccessLinkActionView):
    def post(self, request, *args, **kwargs):
        rejected = self._reject_if_complete()
        if rejected:
            return rejected

        link = self._get_active_link()
        regenerate_client_access_link(link)
        messages.success(request, "Client access link regenerated.")
        return redirect(self.get_redirect_url())
