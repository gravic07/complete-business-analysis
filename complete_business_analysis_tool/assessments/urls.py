"""URL configuration for the assessments application."""

from django.urls import path

from .views import (
    AssessmentAnswerView,
    AssessmentDetailView,
    AssessmentStartView,
    AssessmentTemplateListView,
    CategoryGuidanceView,
    ClientAccessLinkGenerateView,
    ClientAccessLinkRegenerateView,
    ClientAccessLinkRevokeView,
    MarkCompleteView,
)

app_name = "assessments"

urlpatterns = [
    path("", view=AssessmentTemplateListView.as_view(), name="list"),
    path("<uuid:pk>/", view=AssessmentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/answer/", view=AssessmentAnswerView.as_view(), name="answer"),
    path("<uuid:pk>/start/", view=AssessmentStartView.as_view(), name="start"),
    path(
        "<uuid:pk>/guidance/",
        view=CategoryGuidanceView.as_view(),
        name="guidance",
    ),
    path(
        "<uuid:pk>/complete/",
        view=MarkCompleteView.as_view(),
        name="mark_complete",
    ),
    path(
        "<uuid:pk>/access-link/<str:link_type>/generate/",
        view=ClientAccessLinkGenerateView.as_view(),
        name="access_link_generate",
    ),
    path(
        "<uuid:pk>/access-link/<str:link_type>/revoke/",
        view=ClientAccessLinkRevokeView.as_view(),
        name="access_link_revoke",
    ),
    path(
        "<uuid:pk>/access-link/<str:link_type>/regenerate/",
        view=ClientAccessLinkRegenerateView.as_view(),
        name="access_link_regenerate",
    ),
]
