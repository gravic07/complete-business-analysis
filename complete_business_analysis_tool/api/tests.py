from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from complete_business_analysis_tool.clients.models import Client
from complete_business_analysis_tool.users.tests.factories import UserFactory


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
