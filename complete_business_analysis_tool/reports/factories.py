from factory import SelfAttribute, SubFactory
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.assessments.factories import AssessmentFactory
from complete_business_analysis_tool.reports.models import Feedback, PDFExport
from complete_business_analysis_tool.users.tests.factories import UserFactory


class FeedbackFactory(DjangoModelFactory[Feedback]):
    created_by = SubFactory(UserFactory)
    assessment = SubFactory(
        AssessmentFactory,
        created_by=SelfAttribute("..created_by"),
    )

    class Meta:
        model = Feedback


class PDFExportFactory(DjangoModelFactory[PDFExport]):
    created_by = SubFactory(UserFactory)
    assessment = SubFactory(
        AssessmentFactory,
        created_by=SelfAttribute("..created_by"),
    )

    class Meta:
        model = PDFExport
