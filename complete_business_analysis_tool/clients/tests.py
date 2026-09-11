import pytest
from django.core.exceptions import ValidationError
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
