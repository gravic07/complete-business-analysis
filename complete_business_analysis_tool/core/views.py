from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.models import (
    Assessment,
    AssessmentTemplate,
)
from complete_business_analysis_tool.clients.models import Client
from complete_business_analysis_tool.core.middleware import team_not_required


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["client_count"] = Client.objects.count()
        context["template_count"] = AssessmentTemplate.objects.count()
        context["assessment_count"] = Assessment.objects.count()
        context["analysis_count"] = Analysis.objects.filter(
            status=Analysis.Status.COMPLETE,
        ).count()
        return context


@method_decorator(team_not_required, name="dispatch")
class NoTeamView(LoginRequiredMixin, TemplateView):
    """Where `NoTeamGateMiddleware` sends a logged-in User who has no Team."""

    template_name = "pages/no-team.html"
