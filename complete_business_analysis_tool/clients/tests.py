import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.clients.factories import ClientFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


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
