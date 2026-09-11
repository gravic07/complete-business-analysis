from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import (
    AssessmentFactory,
    AssessmentTemplateFactory,
    ClientAccessLinkFactory,
    QuestionFactory,
    QuestionOptionFactory,
    TemplateQuestionFactory,
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


def _make_answer_link(client_email="client@example.com"):
    """Build an ACTIVE Answer-type link on a one-question template."""
    template = AssessmentTemplateFactory.create()
    question = QuestionFactory.create()
    option = QuestionOptionFactory.create(question=question, rank=1)
    TemplateQuestionFactory.create(template=template, question=question)
    assessment = AssessmentFactory.create(
        template=template,
        status=Assessment.Status.DRAFT,
        client=ClientFactory.create(email=client_email),
    )
    link = ClientAccessLinkFactory.create(
        link_type=ClientAccessLink.LinkType.ANSWER,
        status=ClientAccessLink.Status.ACTIVE,
        assessment=assessment,
    )
    return link, question, option


@pytest.mark.django_db
def test_fresh_get_on_active_answer_link_always_renders_email_gate():
    link, _, _ = _make_answer_link()

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert response.status_code == HTTPStatus.OK
    assert b"Enter your email to continue" in response.content


@pytest.mark.django_db
def test_reopening_link_after_verifying_email_returns_to_the_gate_again():
    link, _, _ = _make_answer_link(client_email="client@example.com")
    url = reverse("client_portal:entry", kwargs={"token": link.token})
    http_client = Client()
    http_client.post(url, {"email": "client@example.com"})

    response = http_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert b"Enter your email to continue" in response.content


@pytest.mark.django_db
def test_non_matching_email_returns_generic_denial_revealing_no_assessment_detail():
    link, _, _ = _make_answer_link(client_email="client@example.com")
    assessment = link.assessment
    assessment.client.business_name = "Acme Co"
    assessment.client.save()

    response = Client().post(
        reverse("client_portal:entry", kwargs={"token": link.token}),
        {"email": "wrong@example.com"},
    )

    assert response.status_code == HTTPStatus.OK
    assert b"verify that email for this link" in response.content
    assert b"Acme Co" not in response.content
    assert b"Submit Answers" not in response.content


@pytest.mark.django_db
def test_matching_email_renders_answer_form_with_token_and_email_hidden():
    link, question, _ = _make_answer_link(client_email="client@example.com")

    response = Client().post(
        reverse("client_portal:entry", kwargs={"token": link.token}),
        {"email": "Client@Example.com"},
    )

    assert response.status_code == HTTPStatus.OK
    assert b"Submit Answers" in response.content
    assert f'name="token" value="{link.token}"'.encode() in response.content
    assert b'name="verified_email" value="Client@Example.com"' in response.content
    assert f"question_{question.pk.hex}".encode() in response.content


@pytest.mark.django_db
def test_saving_answer_form_persists_answer_and_advances_draft_to_in_progress():
    link, question, option = _make_answer_link(client_email="client@example.com")
    url = reverse("client_portal:entry", kwargs={"token": link.token})

    response = Client().post(
        url,
        {
            "token": link.token,
            "verified_email": "client@example.com",
            f"question_{question.pk.hex}": str(option.pk),
        },
    )

    assert response.status_code == HTTPStatus.OK
    answer = link.assessment.answers.get()
    assert answer.question == question
    assert answer.selected_option == option
    assert answer.question_snapshot == question.body
    link.assessment.refresh_from_db()
    assert link.assessment.status == Assessment.Status.IN_PROGRESS


@pytest.mark.django_db
def test_saving_answer_form_never_marks_assessment_complete():
    link, question, option = _make_answer_link(client_email="client@example.com")
    link.assessment.status = Assessment.Status.IN_PROGRESS
    link.assessment.save(update_fields=["status"])
    url = reverse("client_portal:entry", kwargs={"token": link.token})

    Client().post(
        url,
        {
            "token": link.token,
            "verified_email": "client@example.com",
            f"question_{question.pk.hex}": str(option.pk),
        },
    )

    link.assessment.refresh_from_db()
    assert link.assessment.status != Assessment.Status.COMPLETE


@pytest.mark.django_db
def test_saving_answer_form_shows_confirmation_message():
    link, question, option = _make_answer_link(client_email="client@example.com")
    url = reverse("client_portal:entry", kwargs={"token": link.token})

    response = Client().post(
        url,
        {
            "token": link.token,
            "verified_email": "client@example.com",
            f"question_{question.pk.hex}": str(option.pk),
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert b"answers have been saved" in response.content
    assert b"return using the same link" in response.content


@pytest.mark.django_db
def test_email_gate_shows_generic_branding_before_verification():
    link, _, _ = _make_answer_link()
    link.assessment.client.business_name = "Acme Co"
    link.assessment.client.save()

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert b"Acme Co" not in response.content
    assert b"Complete Business Analysis Tool" in response.content


@pytest.mark.django_db
def test_verified_answer_form_and_confirmation_show_client_header():
    link, question, option = _make_answer_link(client_email="client@example.com")
    link.assessment.client.business_name = "Acme Co"
    link.assessment.client.save()
    url = reverse("client_portal:entry", kwargs={"token": link.token})
    http_client = Client()

    form_response = http_client.post(url, {"email": "client@example.com"})
    assert b"Acme Co" in form_response.content

    save_response = http_client.post(
        url,
        {
            "token": link.token,
            "verified_email": "client@example.com",
            f"question_{question.pk.hex}": str(option.pk),
        },
    )
    assert b"Acme Co" in save_response.content


@pytest.mark.django_db
def test_answer_submission_with_mismatched_verified_email_is_sent_back_to_gate():
    link, question, option = _make_answer_link(client_email="client@example.com")
    url = reverse("client_portal:entry", kwargs={"token": link.token})

    response = Client().post(
        url,
        {
            "token": link.token,
            "verified_email": "someone-else@example.com",
            f"question_{question.pk.hex}": str(option.pk),
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert b"Enter your email to continue" in response.content
    assert link.assessment.answers.count() == 0


@pytest.mark.django_db
def test_portal_pages_include_beforeunload_unsaved_changes_guard():
    link, _, _ = _make_answer_link()

    response = Client().get(
        reverse("client_portal:entry", kwargs={"token": link.token}),
    )

    assert b"beforeunload" in response.content
    assert b"isn't valid" not in response.content
