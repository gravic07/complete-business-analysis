from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

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


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "pages/clients/client-form.html"
    success_url = reverse_lazy("clients:list")
