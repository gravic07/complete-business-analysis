from http import HTTPStatus

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from rest_framework.test import APIClient

from complete_business_analysis_tool.api.permissions import HasTeam
from complete_business_analysis_tool.clients.models import Client
from complete_business_analysis_tool.users.tests.factories import UserFactory

# API routes that deliberately don't require a Team: obtaining a token needs no
# auth at all, and the schema/docs are gated by SPECTACULAR SERVE_PERMISSIONS.
TEAM_EXEMPT_API_ROUTES = {"obtain_auth_token", "api-schema", "api-docs"}


def _api_routes(patterns=None, prefix=""):
    """Yield (path, name, view callback) for every URL pattern under `/api/`."""
    for pattern in get_resolver().url_patterns if patterns is None else patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from _api_routes(pattern.url_patterns, route)
        elif isinstance(pattern, URLPattern) and route.startswith("api/"):
            yield route, pattern.name, pattern.callback


def test_every_api_view_requires_a_team():
    unguarded = [
        route
        for route, name, callback in _api_routes()
        if name not in TEAM_EXEMPT_API_ROUTES
        and HasTeam not in callback.cls.permission_classes
    ]

    assert unguarded == []


@pytest.mark.django_db
def test_api_client_create_stamps_creators_team_and_created_by():
    user = UserFactory.create()
    api_client = APIClient()
    api_client.force_authenticate(user)

    response = api_client.post(
        reverse("api:client-create"),
        {
            "business_name": "Acme Co",
            "first_name": "Jane",
            "last_name": "Doe",
            "title": "CEO",
            "industry": "technology",
            "company_size": "5_19",
            "revenue": "under_1m",
            "corporate_style": "partnership",
        },
        format="json",
    )

    assert response.status_code == HTTPStatus.CREATED
    client = Client.objects.get(pk=response.json()["id"])
    assert client.team == user.team
    assert client.created_by == user
