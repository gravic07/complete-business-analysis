from django.urls import path

from .views import (
    AnalysisStatusView,
    PDFExportStatusView,
    PDFTemplateView,
    ReportView,
    SubmitFeedbackView,
    TriggerAnalysisView,
    TriggerPDFExportView,
    UpdateAssessmentNameView,
)

app_name = "reports"

urlpatterns = [
    path("<uuid:pk>/", ReportView.as_view(), name="report"),
    path("<uuid:pk>/feedback/", SubmitFeedbackView.as_view(), name="submit_feedback"),
    path("<uuid:pk>/pdf/", PDFTemplateView.as_view(), name="pdf"),
    path("<uuid:pk>/rename/", UpdateAssessmentNameView.as_view(), name="rename"),
    path("<uuid:pk>/export-pdf/", TriggerPDFExportView.as_view(), name="export_pdf"),
    path("<uuid:pk>/generate/", TriggerAnalysisView.as_view(), name="generate_analysis"),
    path(
        "pdf-export/<uuid:pk>/status/",
        PDFExportStatusView.as_view(),
        name="pdf_export_status",
    ),
    path(
        "analysis/<uuid:pk>/status/",
        AnalysisStatusView.as_view(),
        name="analysis_status",
    ),
]
