import contextlib
from http import HTTPStatus
from importlib import reload

import pytest
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from complete_business_analysis_tool.teams.factories import TeamFactory
from complete_business_analysis_tool.users.models import User
from complete_business_analysis_tool.users.tests.factories import UserFactory


class TestUserAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_search(self, admin_client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:users_user_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = admin_client.post(
            url,
            data={
                "email": "new-admin@example.com",
                "password1": "My_R@ndom-P@ssw0rd",
                "password2": "My_R@ndom-P@ssw0rd",
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        assert User.objects.filter(email="new-admin@example.com").exists()

    def test_view_user(self, admin_client):
        user = User.objects.get(email="admin@example.com")
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_changelist_filters_by_team(self, admin_client):
        team = TeamFactory.create()
        member = UserFactory.create(team=team)
        outsider = UserFactory.create()
        url = reverse("admin:users_user_changelist")

        response = admin_client.get(url, data={"team__id__exact": str(team.pk)})

        users = list(response.context["cl"].result_list)
        assert member in users
        assert outsider not in users

    @pytest.mark.parametrize(
        ("starts_in_team", "ends_in_team"),
        [(False, True), (True, True), (True, False)],
        ids=["assign", "move", "clear"],
    )
    def test_change_form_sets_team(self, admin_client, starts_in_team, ends_in_team):
        original = TeamFactory.create() if starts_in_team else None
        target = TeamFactory.create() if ends_in_team else None
        user = UserFactory.create(team=original)
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})

        response = admin_client.post(
            url,
            data={
                "email": user.email,
                "name": user.name,
                "team": str(target.pk) if target else "",
                "is_active": "on",
                "date_joined_0": "2026-01-01",
                "date_joined_1": "00:00:00",
            },
        )

        assert response.status_code == HTTPStatus.FOUND
        user.refresh_from_db()
        assert user.team == target

    @pytest.fixture
    def _force_allauth(self, settings):
        settings.DJANGO_ADMIN_FORCE_ALLAUTH = True
        # Reload the admin module to apply the setting change
        import complete_business_analysis_tool.users.admin as users_admin  # noqa: PLC0415

        with contextlib.suppress(admin.sites.AlreadyRegistered):  # type: ignore[attr-defined]
            reload(users_admin)

    @pytest.mark.django_db
    @pytest.mark.usefixtures("_force_allauth")
    def test_allauth_login(self, rf, settings):
        request = rf.get("/fake-url")
        request.user = AnonymousUser()
        response = admin.site.login(request)

        # The `admin` login view should redirect to the `allauth` login view
        target_url = reverse(settings.LOGIN_URL) + "?next=" + request.path
        assertRedirects(response, target_url, fetch_redirect_response=False)
