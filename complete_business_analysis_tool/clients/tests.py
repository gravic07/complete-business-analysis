from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.clients.models import Client as ClientModel
from complete_business_analysis_tool.clients.models import (
    CompanySize,
    CorporateStyle,
    IndustryType,
    RevenueRange,
)
from complete_business_analysis_tool.teams.factories import TeamFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


def test_client_email_is_optional():
    field = ClientModel.email.field

    field.clean("", model_instance=None)


def test_client_email_rejects_invalid_format():
    field = ClientModel.email.field

    with pytest.raises(ValidationError):
        field.clean("not-an-email", model_instance=None)


def test_client_email_accepts_valid_format():
    field = ClientModel.email.field

    field.clean("client@example.com", model_instance=None)


@pytest.mark.django_db
def test_client_email_has_no_uniqueness_constraint():
    ClientFactory.create(email="shared@example.com")
    second_client = ClientFactory.create(email="shared@example.com")

    expected_client_count = 2
    assert (
        ClientModel.objects.filter(email="shared@example.com").count()
        == expected_client_count
    )
    assert second_client.email == "shared@example.com"


@pytest.mark.django_db
def test_client_edit_form_renders_email_field():
    client_obj = ClientFactory.create(email="")
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("clients:edit", kwargs={"pk": client_obj.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert 'name="email"' in content


@pytest.mark.django_db
def test_client_edit_form_saves_email():
    client_obj = ClientFactory.create(email="")
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("clients:edit", kwargs={"pk": client_obj.pk})
    http_client.post(
        url,
        {
            "business_name": client_obj.business_name,
            "first_name": client_obj.first_name,
            "last_name": client_obj.last_name,
            "title": client_obj.title,
            "email": "client@example.com",
            "industry": IndustryType.TECHNOLOGY,
            "company_size": CompanySize.SMALL,
            "revenue": RevenueRange.UNDER_1M,
            "corporate_style": CorporateStyle.SOLE_PROPRIETORSHIP,
        },
    )

    client_obj.refresh_from_db()
    assert client_obj.email == "client@example.com"


@pytest.mark.django_db
def test_client_detail_includes_report_link_for_each_assessment():
    client_obj = ClientFactory.create()
    assessment = AssessmentFactory.create(client=client_obj)

    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("clients:detail", kwargs={"pk": client_obj.pk})
    response = http_client.get(url)

    expected_url = reverse("reports:report", kwargs={"pk": assessment.pk})
    assert expected_url in response.content.decode()


def _client_form_data(**overrides):
    data = {
        "business_name": "Acme Co",
        "first_name": "Jane",
        "last_name": "Doe",
        "title": "CEO",
        "email": "",
        "industry": IndustryType.TECHNOLOGY,
        "company_size": CompanySize.SMALL,
        "revenue": RevenueRange.UNDER_1M,
        "corporate_style": CorporateStyle.SOLE_PROPRIETORSHIP,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_client_create_stamps_creators_team_and_created_by():
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    response = http_client.post(reverse("clients:create"), _client_form_data())

    assert response.status_code == HTTPStatus.FOUND
    client_obj = ClientModel.objects.get(business_name="Acme Co")
    assert client_obj.team == user.team
    assert client_obj.created_by == user


@pytest.mark.django_db
def test_client_create_ignores_posted_team():
    user = UserFactory.create()
    other_team = TeamFactory.create()
    http_client = Client()
    http_client.force_login(user)

    http_client.post(
        reverse("clients:create"),
        _client_form_data(team=str(other_team.pk)),
    )

    assert ClientModel.objects.get(business_name="Acme Co").team == user.team


@pytest.mark.django_db
def test_client_form_has_no_team_field():
    user = UserFactory.create()
    http_client = Client()
    http_client.force_login(user)

    response = http_client.get(reverse("clients:create"))

    assert 'name="team"' not in response.content.decode()


@pytest.mark.django_db
def test_client_edit_keeps_original_team_and_created_by():
    creator = UserFactory.create()
    client_obj = ClientFactory.create(created_by=creator)
    editor = UserFactory.create(team=creator.team)
    http_client = Client()
    http_client.force_login(editor)

    http_client.post(
        reverse("clients:edit", kwargs={"pk": client_obj.pk}),
        _client_form_data(business_name="Renamed Co"),
    )

    client_obj.refresh_from_db()
    assert client_obj.business_name == "Renamed Co"
    assert client_obj.created_by == creator
    assert client_obj.team == creator.team


@pytest.mark.django_db
def test_client_factory_derives_team_from_created_by():
    user = UserFactory.create()

    assert ClientFactory.create(created_by=user).team == user.team


@pytest.mark.django_db
def test_deleting_user_who_created_a_client_is_refused():
    user = UserFactory.create()
    ClientFactory.create(created_by=user)

    with pytest.raises(ProtectedError):
        user.delete()


@pytest.mark.django_db
def test_deleting_team_that_owns_a_client_is_refused():
    client_obj = ClientFactory.create()
    client_obj.created_by.team = None
    client_obj.created_by.save()

    with pytest.raises(ProtectedError):
        client_obj.team.delete()


@pytest.mark.django_db
def test_admin_client_changelist_shows_team_and_created_by(admin_client):
    client_obj = ClientFactory.create()

    response = admin_client.get(
        reverse("admin:clients_client_changelist"),
        {"team__id__exact": str(client_obj.team.pk)},
    )

    content = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "column-team" in content
    assert "column-created_by" in content
    assert client_obj.business_name in content


@pytest.mark.django_db
def test_admin_can_move_client_to_another_team(admin_client):
    client_obj = ClientFactory.create()
    target = TeamFactory.create()
    url = reverse("admin:clients_client_change", kwargs={"object_id": client_obj.pk})

    response = admin_client.post(
        url,
        {
            **_client_form_data(),
            "team": str(target.pk),
            "created_by": str(client_obj.created_by.pk),
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    client_obj.refresh_from_db()
    assert client_obj.team == target
