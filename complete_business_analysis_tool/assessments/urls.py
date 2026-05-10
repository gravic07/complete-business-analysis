"""URL configuration for the assessments application."""

from django.urls import path

from .views import AssessmentDetailView, AssessmentEntryView, AssessmentTemplateListView

app_name = "assessments"

urlpatterns = [
    path("", view=AssessmentTemplateListView.as_view(), name="list"),
    path("<uuid:pk>/", view=AssessmentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/entry/", view=AssessmentEntryView.as_view(), name="entry"),
]
