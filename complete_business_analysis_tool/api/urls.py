"""URL configuration for the api application."""

from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from complete_business_analysis_tool.users.api.views import UserViewSet

from .views.clients import ClientCreateView

router = DefaultRouter() if settings.DEBUG else SimpleRouter()
router.register("users", UserViewSet)

app_name = "api"
urlpatterns = [
    *router.urls,
    path("clients/create/", ClientCreateView.as_view(), name="client-create"),
]
