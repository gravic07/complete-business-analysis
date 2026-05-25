from factory import Faker
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.clients.models import Client, IndustryType


class ClientFactory(DjangoModelFactory[Client]):
    business_name = Faker("company")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    title = Faker("job")
    industry = IndustryType.TECHNOLOGY

    class Meta:
        model = Client
