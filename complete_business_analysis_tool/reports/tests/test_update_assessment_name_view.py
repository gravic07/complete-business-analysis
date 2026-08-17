import http

import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_post_valid_name_saves_and_returns_200():
    assessment = AssessmentFactory.create()
    user = UserFactory.create()
    client = Client()
    client.force_login(user)

    url = reverse("reports:rename", kwargs={"pk": assessment.pk})
    response = client.post(url, {"name": "Q4 Analysis"})

    assert response.status_code == http.HTTPStatus.OK
    assessment.refresh_from_db()
    assert assessment.name == "Q4 Analysis"


@pytest.mark.django_db
def test_post_empty_name_is_rejected():
    assessment = AssessmentFactory.create(name="Original Name")
    user = UserFactory.create()
    client = Client()
    client.force_login(user)

    url = reverse("reports:rename", kwargs={"pk": assessment.pk})
    response = client.post(url, {"name": ""})

    assert response.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY
    assessment.refresh_from_db()
    assert assessment.name == "Original Name"
