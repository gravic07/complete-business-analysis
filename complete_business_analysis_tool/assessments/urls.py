"""URL configuration for the assessments application."""

from django.urls import path

from .views import AssessmentEntryView, AssessmentTemplateListView

app_name = "assessments"

urlpatterns = [
    path("", view=AssessmentTemplateListView.as_view(), name="list"),
    path("<uuid:pk>/entry/", view=AssessmentEntryView.as_view(), name="entry"),
]
