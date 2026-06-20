from django.urls import path

from .views import (
    PDFTemplateView,
    ReportView,
    SubmitFeedbackView,
    UpdateAssessmentNameView,
)

app_name = "reports"

urlpatterns = [
    path("<uuid:pk>/", ReportView.as_view(), name="report"),
    path("<uuid:pk>/feedback/", SubmitFeedbackView.as_view(), name="submit_feedback"),
    path("<uuid:pk>/pdf/", PDFTemplateView.as_view(), name="pdf"),
    path("<uuid:pk>/rename/", UpdateAssessmentNameView.as_view(), name="rename"),
]
