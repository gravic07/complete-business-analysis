from django.urls import path

from .views import ReportView, SubmitFeedbackView

app_name = "reports"

urlpatterns = [
    path("<uuid:pk>/", ReportView.as_view(), name="report"),
    path("<uuid:pk>/feedback/", SubmitFeedbackView.as_view(), name="submit_feedback"),
]
