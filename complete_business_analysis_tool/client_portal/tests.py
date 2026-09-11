from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    ClientAccessLinkFactory,
)
from complete_business_analysis_tool.assessments.models import (
    Assessment,
    ClientAccessLink,
)
from complete_business_analysis_tool.clients.factories import ClientFactory


@pytest.mark.django_db
def test_unrecognized_token_renders_generic_invalid_page():
    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": "not-a-real-token"}),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert b"isn't valid" in response.content
    assert b"contact your advisor" not in response.content


@pytest.mark.django_db
def test_revoked_link_renders_friendly_deactivated_page():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.REVOKED,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(business_name="Acme Co"),
        ),
    )

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert response.status_code == HTTPStatus.OK
    assert b"no longer active" in response.content
    assert b"contact your advisor" in response.content


@pytest.mark.django_db
def test_link_on_complete_assessment_renders_deactivated_page_despite_active_status():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.COMPLETE),
    )

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert response.status_code == HTTPStatus.OK
    assert b"no longer active" in response.content
    link.refresh_from_db()
    assert link.status == ClientAccessLink.Status.ACTIVE


@pytest.mark.django_db
def test_deactivated_page_shows_client_contact_and_business_name_in_header():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.REVOKED,
        assessment=AssessmentFactory.create(
            client=ClientFactory.create(
                business_name="Acme Co",
                first_name="Jamie",
                last_name="Rivera",
            ),
        ),
    )

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert b"Acme Co" in response.content
    assert b"Jamie" in response.content
    assert b"Rivera" in response.content


@pytest.mark.django_db
def test_terminal_pages_render_no_staff_navigation():
    link = ClientAccessLinkFactory.create(status=ClientAccessLink.Status.REVOKED)

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert b"navbar-menu" not in response.content
    assert b"Assessments</a>" not in response.content


@pytest.mark.django_db
def test_active_link_on_in_progress_assessment_does_not_render_terminal_page():
    link = ClientAccessLinkFactory.create(
        status=ClientAccessLink.Status.ACTIVE,
        assessment=AssessmentFactory.create(status=Assessment.Status.IN_PROGRESS),
    )

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert response.status_code == HTTPStatus.OK
    assert b"no longer active" not in response.content
    assert b"isn't valid" not in response.content
