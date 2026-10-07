from http import HTTPStatus

import pytest
from django.db.models import ProtectedError
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.teams.factories import TeamFactory
from complete_business_analysis_tool.teams.models import Team
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_navbar_shows_team_name_for_team_member():
    user = UserFactory.create(team=TeamFactory.create(name="Summit Advisors"))
    http_client = Client()
    http_client.force_login(user)

    response = http_client.get(reverse("home"))

    assert "Summit Advisors" in response.content.decode()


@pytest.mark.django_db
def test_navbar_shows_no_team_for_user_without_team():
    user = UserFactory.create(team=None)
    http_client = Client()
    http_client.force_login(user)

    response = http_client.get(reverse("no_team"))

    assert response.status_code == HTTPStatus.OK
    assert 'data-testid="navbar-team"' not in response.content.decode()


@pytest.mark.django_db
def test_deleting_team_with_members_is_refused():
    team = TeamFactory.create()
    UserFactory.create(team=team)

    with pytest.raises(ProtectedError):
        team.delete()


@pytest.mark.django_db
def test_platform_admin_can_create_team_in_admin(admin_client):
    response = admin_client.post(
        reverse("admin:teams_team_add"),
        {"name": "Summit Advisors"},
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Team.objects.filter(name="Summit Advisors").exists()


@pytest.mark.django_db
def test_user_factory_assigns_team_by_default():
    assert UserFactory.create().team is not None
