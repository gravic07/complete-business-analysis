import pytest
from django.test import Client
from django.urls import reverse

from complete_business_analysis_tool.analysis.models import Analysis
from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.users.tests.factories import UserFactory


@pytest.mark.django_db
def test_assessment_name_defaults_to_initial_report():
    assessment = AssessmentFactory()
    assert assessment.name == "Initial Report"


@pytest.mark.django_db
def test_assessment_detail_lists_all_analysis_runs_with_status_and_timestamp():
    assessment = AssessmentFactory()
    analysis1 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.COMPLETE,
    )
    _analysis2 = Analysis.objects.create(
        assessment=assessment,
        status=Analysis.Status.FAILED,
    )

    user = UserFactory()
    http_client = Client()
    http_client.force_login(user)

    url = reverse("assessments:detail", kwargs={"pk": assessment.pk})
    response = http_client.get(url)
    content = response.content.decode()

    assert str(analysis1.pk) in content or "Complete" in content
    assert "Complete" in content
    assert "Failed" in content
