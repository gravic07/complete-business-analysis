"""Views for the public, unauthenticated client_portal application."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from complete_business_analysis_tool.assessments.models import ClientAccessLink
from complete_business_analysis_tool.assessments.services import (
    client_access_link_grants_access,
)


class ClientAccessLinkEntryView(View):
    """Single token-keyed entry point a Client's link resolves into.

    Resolves the three terminal states (unrecognized token, revoked link,
    link on a completed Assessment). The email gate and per-step form flows
    for a still-valid link land in tickets 04-05.
    """

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        link = (
            ClientAccessLink.objects.select_related("assessment__client")
            .filter(token=token)
            .first()
        )
        if link is None:
            return render(
                request,
                "pages/client_portal/invalid-link.html",
                status=404,
            )

        if not client_access_link_grants_access(link):
            return render(
                request,
                "pages/client_portal/deactivated-link.html",
                {"client": link.assessment.client},
            )

        return HttpResponse("This step isn't available here yet.")
