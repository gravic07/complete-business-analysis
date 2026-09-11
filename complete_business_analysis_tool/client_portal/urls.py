"""URL configuration for the client_portal application."""

from django.urls import path

from .views import ClientAccessLinkEntryView

app_name = "client_portal"

urlpatterns = [
    path("<str:token>/", view=ClientAccessLinkEntryView.as_view(), name="entry"),
]
