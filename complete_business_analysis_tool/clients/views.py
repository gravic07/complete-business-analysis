from django.db.models import Count, OuterRef, Subquery, Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from complete_business_analysis_tool.assessments.models import Answer

from .forms import ClientForm
from .models import Client


class ClientListView(ListView):
    model = Client
    template_name = "pages/clients/client-list.html"
    context_object_name = "clients"
    ordering = ["business_name"]

    def get_queryset(self):
        return super().get_queryset().annotate(assessment_count=Count("assessments"))


class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = "pages/clients/client-form.html"
    success_url = reverse_lazy("clients:list")


class ClientDetailView(DetailView):
    model = Client
    template_name = "pages/clients/client-detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        score_subquery = (
            Answer.objects.filter(assessment=OuterRef("pk"))
            .values("assessment")
            .annotate(total=Sum("selected_option__rank"))
            .values("total")
        )
        context["assessments"] = (
            self.object.assessments.select_related("template")
            .annotate(
                question_count=Count("template__template_questions", distinct=True),
                score=Subquery(score_subquery),
            )
            .order_by("-created_at")
        )
        return context


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "pages/clients/client-form.html"
    success_url = reverse_lazy("clients:list")
