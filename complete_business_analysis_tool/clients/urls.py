"""URL configuration for the clients application."""

from django.urls import path

from .views import ClientCreateView, ClientDetailView, ClientListView, ClientUpdateView

app_name = "clients"

urlpatterns = [
    path("", view=ClientListView.as_view(), name="list"),
    path("create/", view=ClientCreateView.as_view(), name="create"),
    path("<uuid:pk>/", view=ClientDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", view=ClientUpdateView.as_view(), name="edit"),
]
