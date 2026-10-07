from http import HTTPStatus

import pytest
from django.core.signing import TimestampSigner
from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token

from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    ClientAccessLinkFactory,
)
from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.clients.models import Client as ClientModel
from complete_business_analysis_tool.teams.factories import TeamFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "needs_pk"),
    [
        ("clients:list", False),
        ("clients:create", False),
        ("clients:detail", True),
        ("clients:edit", True),
    ],
)
def test_anonymous_request_to_client_pages_redirects_to_login(url_name, needs_pk):
    kwargs = {"pk": ClientFactory.create().pk} if needs_pk else {}
    url = reverse(url_name, kwargs=kwargs)
    http_client = Client()

    response = http_client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == f"{reverse('account_login')}?next={url}"


@pytest.mark.django_db
def test_anonymous_post_to_client_create_redirects_to_login_without_saving():
    http_client = Client()

    response = http_client.post(reverse("clients:create"), {"business_name": "Acme"})

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"].startswith(reverse("account_login"))
    assert not ClientModel.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "kwargs"),
    [
        ("account_login", {}),
        ("account_signup", {}),
        ("account_reset_password", {}),
        ("account_reset_password_done", {}),
        ("account_email_verification_sent", {}),
        ("account_confirm_email", {"key": "not-a-real-key"}),
        ("account_reset_password_from_key", {"uidb36": "0", "key": "bad-key"}),
    ],
)
def test_allauth_account_pages_remain_reachable_anonymously(url_name, kwargs):
    http_client = Client()

    response = http_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_token_authenticated_api_request_succeeds():
    user = UserFactory.create()
    token = Token.objects.create(user=user)
    http_client = Client()

    response = http_client.get(
        reverse("api:user-me"),
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["api:user-me", "api:client-create"])
def test_unauthenticated_api_request_gets_drf_denial_not_login_redirect(url_name):
    http_client = Client()

    response = http_client.get(reverse(url_name))

    assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
    assert "Location" not in response


def _logged_in_client(user):
    http_client = Client()
    http_client.force_login(user)
    return http_client


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["home", "clients:list", "assessments:list"])
def test_user_without_team_is_redirected_to_no_team_page(url_name):
    http_client = _logged_in_client(UserFactory.create(team=None))

    response = http_client.get(reverse(url_name))

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == reverse("no_team")


@pytest.mark.django_db
def test_anonymous_request_to_no_team_page_redirects_to_login():
    url = reverse("no_team")

    response = Client().get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == f"{reverse('account_login')}?next={url}"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    ["account_logout", "account_change_password", "account_email", "mfa_index"],
)
def test_user_without_team_can_reach_allauth_account_pages(url_name):
    http_client = _logged_in_client(UserFactory.create(team=None))

    response = http_client.get(reverse(url_name))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_user_without_team_can_view_and_edit_their_profile():
    user = UserFactory.create(team=None)
    http_client = _logged_in_client(user)

    detail = http_client.get(reverse("users:detail", kwargs={"pk": user.pk}))
    update = http_client.get(reverse("users:update"))
    redirect = http_client.get(reverse("users:redirect"))

    assert detail.status_code == HTTPStatus.OK
    assert update.status_code == HTTPStatus.OK
    assert redirect["Location"] == reverse("users:detail", kwargs={"pk": user.pk})


@pytest.mark.django_db
def test_user_without_team_can_log_out():
    http_client = _logged_in_client(UserFactory.create(team=None))

    http_client.post(reverse("account_logout"))

    assert "_auth_user_id" not in http_client.session


@pytest.mark.django_db
def test_staff_user_without_team_can_use_admin():
    http_client = _logged_in_client(
        UserFactory.create(team=None, is_staff=True, is_superuser=True),
    )

    response = http_client.get(reverse("admin:index"))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("has_team", [False, True])
def test_client_portal_is_unaffected_by_team_gate(has_team):
    user = UserFactory.create() if has_team else UserFactory.create(team=None)
    link = ClientAccessLinkFactory.create()
    url = reverse("client_portal:entry", kwargs={"token": link.token})

    anonymous_response = Client().get(url)
    logged_in_response = _logged_in_client(user).get(url)

    assert anonymous_response.status_code == HTTPStatus.OK
    assert logged_in_response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_pdf_template_signed_token_path_is_unaffected_by_team_gate():
    assessment = AssessmentFactory.create()
    token = TimestampSigner().sign(str(assessment.pk))

    response = Client().get(
        reverse("reports:pdf", kwargs={"pk": assessment.pk}),
        {"token": token},
    )

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_pdf_template_is_reachable_for_logged_in_user_without_team():
    assessment = AssessmentFactory.create()
    http_client = _logged_in_client(UserFactory.create(team=None))

    response = http_client.get(reverse("reports:pdf", kwargs={"pk": assessment.pk}))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_api_request_from_user_without_team_gets_403_json():
    http_client = _logged_in_client(UserFactory.create(team=None))

    response = http_client.get(reverse("api:user-me"))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["Content-Type"] == "application/json"
    assert "team" in response.json()["detail"].lower()


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_token_api_request_from_user_without_team_gets_403_json(method):
    token = Token.objects.create(user=UserFactory.create(team=None))
    http_client = Client()

    response = getattr(http_client, method)(
        reverse("api:client-create"),
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "team" in response.json()["detail"].lower()
    assert not ClientModel.objects.exists()


@pytest.mark.django_db
def test_invalid_token_api_request_is_left_to_drf():
    http_client = Client()

    response = http_client.get(
        reverse("api:user-me"),
        HTTP_AUTHORIZATION="Token not-a-real-token",
    )

    assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
    assert "team" not in response.json()["detail"].lower()


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["home", "clients:list", "no_team"])
def test_user_with_team_is_never_redirected(url_name):
    http_client = _logged_in_client(UserFactory.create())

    response = http_client.get(reverse(url_name))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_api_request_from_user_with_team_is_allowed():
    http_client = _logged_in_client(UserFactory.create())

    response = http_client.get(reverse("api:user-me"))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_user_assigned_to_team_reaches_app_on_next_request():
    user = UserFactory.create(team=None)
    http_client = _logged_in_client(user)
    assert http_client.get(reverse("home")).status_code == HTTPStatus.FOUND

    user.team = TeamFactory.create()
    user.save()

    assert http_client.get(reverse("home")).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_navbar_hides_team_links_for_user_without_team():
    http_client = _logged_in_client(UserFactory.create(team=None))

    content = http_client.get(reverse("no_team")).content.decode()

    assert 'data-testid="navbar-team"' not in content
    assert f'href="{reverse("clients:list")}"' not in content
    assert f'href="{reverse("assessments:list")}"' not in content
    assert "My Profile" in content
    assert f'action="{reverse("account_logout")}"' in content


@pytest.mark.django_db
def test_navbar_shows_team_links_for_team_member():
    http_client = _logged_in_client(
        UserFactory.create(team=TeamFactory.create(name="Summit Advisors")),
    )

    content = http_client.get(reverse("home")).content.decode()

    assert 'data-testid="navbar-team"' in content
    assert "Summit Advisors" in content
    assert f'href="{reverse("clients:list")}"' in content
    assert f'href="{reverse("assessments:list")}"' in content
