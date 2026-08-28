"""URL configuration for the assessments application."""

from django.urls import path

from .views import (
    AssessmentAnswerView,
    AssessmentDetailView,
    AssessmentStartView,
    AssessmentTemplateListView,
    CategoryGuidanceView,
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
]
