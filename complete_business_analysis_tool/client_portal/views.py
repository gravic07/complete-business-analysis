"""Views for the public, unauthenticated client_portal application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.views import View

from complete_business_analysis_tool.assessments.forms import (
    AssessmentAnswerForm,
    CategoryGuidanceForm,
)
from complete_business_analysis_tool.assessments.models import (
    Assessment,
    CategoryGuidance,
    ClientAccessLink,
)
from complete_business_analysis_tool.assessments.services import (
    categories_for_template,
    client_access_link_grants_access,
    save_category_guidance,
)

from .forms import ClientEmailGateForm

if TYPE_CHECKING:
    from complete_business_analysis_tool.clients.models import Client

EMAIL_DENIAL_MESSAGE = (
    "We couldn't verify that email for this link. Please double-check it and try again."
)


def _email_matches(client: Client, submitted_email: str) -> bool:
    if not client.email:
        return False
    return submitted_email.strip().lower() == client.email.strip().lower()


class ClientAccessLinkEntryView(View):
    """Single token-keyed entry point a Client's link resolves into.

    Resolves the three terminal states (unrecognized token, revoked link,
    link on a completed Assessment), then dispatches internally on the
    link's type to either the Answer Questions flow or the Concerns,
    Priorities and Goals (Guidance) flow.

    The email gate never consults a session or cookie: every GET renders a
    fresh gate, and the verified email is only carried forward as a hidden
    field on the underlying form's own POST, re-checked against the live
    Client.email each time.
    """

    link: ClientAccessLink

    def dispatch(
        self,
        request: HttpRequest,
        token: str,
        *args,
        **kwargs,
    ) -> HttpResponseBase:
        link, terminal = self._resolve_link(request, token)
        if terminal is not None or link is None:
            return terminal or HttpResponse(status=404)

        self.link = link
        return super().dispatch(request, token, *args, **kwargs)

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        return self._render_gate(request)

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        if "verified_email" not in request.POST:
            return self._handle_email_check(request)
        if self.link.link_type == ClientAccessLink.LinkType.GUIDANCE:
            return self._handle_guidance_submission(request)
        return self._handle_answer_submission(request)

    @staticmethod
    def _resolve_link(
        request: HttpRequest,
        token: str,
    ) -> tuple[ClientAccessLink | None, HttpResponse | None]:
        link = (
            ClientAccessLink.objects.select_related("assessment__client")
            .filter(token=token)
            .first()
        )
        if link is None:
            return None, render(
                request,
                "pages/client_portal/invalid-link.html",
                status=404,
            )

        if not client_access_link_grants_access(link):
            return None, render(
                request,
                "pages/client_portal/deactivated-link.html",
                {"client": link.assessment.client},
            )

        return link, None

    @property
    def categories(self):
        return categories_for_template(self.link.assessment.template)

    def _render_gate(
        self,
        request: HttpRequest,
        gate_form: ClientEmailGateForm | None = None,
    ) -> HttpResponse:
        template = (
            "pages/client_portal/guidance-gate.html"
            if self.link.link_type == ClientAccessLink.LinkType.GUIDANCE
            else "pages/client_portal/answer-gate.html"
        )
        return render(
            request,
            template,
            {"gate_form": gate_form or ClientEmailGateForm()},
        )

    def _handle_email_check(self, request: HttpRequest) -> HttpResponse:
        gate_form = ClientEmailGateForm(request.POST)
        if not gate_form.is_valid():
            return self._render_gate(request, gate_form)

        submitted_email = gate_form.cleaned_data["email"]
        if not _email_matches(self.link.assessment.client, submitted_email):
            gate_form.add_error(None, EMAIL_DENIAL_MESSAGE)
            return self._render_gate(request, gate_form)

        if self.link.link_type == ClientAccessLink.LinkType.GUIDANCE:
            return self._render_guidance_form(request, verified_email=submitted_email)
        return self._render_answer_form(request, verified_email=submitted_email)

    def _handle_answer_submission(self, request: HttpRequest) -> HttpResponse:
        verified_email = request.POST.get("verified_email", "")
        if request.POST.get("token") != self.link.token or not _email_matches(
            self.link.assessment.client,
            verified_email,
        ):
            return self._render_gate(request)

        assessment = self.link.assessment
        answer_form = AssessmentAnswerForm(request.POST, assessment=assessment)
        if not answer_form.is_valid():
            return self._render_answer_form(
                request,
                verified_email=verified_email,
                answer_form=answer_form,
            )

        answer_form.save()
        return render(
            request,
            "pages/client_portal/answer-saved.html",
            {"assessment": assessment, "client": assessment.client},
        )

    def _render_answer_form(
        self,
        request: HttpRequest,
        verified_email: str,
        answer_form: AssessmentAnswerForm | None = None,
    ) -> HttpResponse:
        assessment: Assessment = self.link.assessment
        if answer_form is None:
            initial = {}
            for answer in assessment.answers.select_related("question"):
                if answer.question and answer.selected_option_id:
                    initial[f"question_{answer.question.pk.hex}"] = str(
                        answer.selected_option_id,
                    )
            answer_form = AssessmentAnswerForm(assessment=assessment, initial=initial)

        return render(
            request,
            "pages/client_portal/answer-questions.html",
            {
                "form": answer_form,
                "assessment": assessment,
                "client": assessment.client,
                "token": self.link.token,
                "verified_email": verified_email,
            },
        )

    def _handle_guidance_submission(self, request: HttpRequest) -> HttpResponse:
        verified_email = request.POST.get("verified_email", "")
        if request.POST.get("token") != self.link.token or not _email_matches(
            self.link.assessment.client,
            verified_email,
        ):
            return self._render_gate(request)

        assessment = self.link.assessment
        categories = self.categories
        guidance_form = CategoryGuidanceForm(request.POST, categories=categories)
        if not guidance_form.is_valid():
            return self._render_guidance_form(
                request,
                verified_email=verified_email,
                guidance_form=guidance_form,
            )

        save_category_guidance(assessment, categories, guidance_form.cleaned_data)
        return render(
            request,
            "pages/client_portal/guidance-saved.html",
            {"assessment": assessment, "client": assessment.client},
        )

    def _render_guidance_form(
        self,
        request: HttpRequest,
        verified_email: str,
        guidance_form: CategoryGuidanceForm | None = None,
    ) -> HttpResponse:
        assessment: Assessment = self.link.assessment
        if guidance_form is None:
            categories = self.categories
            existing_text = dict(
                CategoryGuidance.objects.filter(assessment=assessment).values_list(
                    "category_id",
                    "text",
                ),
            )
            initial = {
                f"category_{category.pk.hex}": existing_text[category.pk]
                for category in categories
                if existing_text.get(category.pk)
            }
            guidance_form = CategoryGuidanceForm(categories=categories, initial=initial)

        return render(
            request,
            "pages/client_portal/concerns-priorities-goals.html",
            {
                "form": guidance_form,
                "assessment": assessment,
                "client": assessment.client,
                "token": self.link.token,
                "verified_email": verified_email,
            },
        )
