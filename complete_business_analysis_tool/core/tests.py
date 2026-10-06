from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token

from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.clients.models import Client as ClientModel
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
