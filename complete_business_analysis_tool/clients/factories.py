from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.clients.models import Client, IndustryType
from complete_business_analysis_tool.users.tests.factories import UserFactory


class ClientFactory(DjangoModelFactory[Client]):
    """Produces a Client owned by its ``created_by`` User's Team."""

    business_name = Faker("company")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    title = Faker("job")
    industry = IndustryType.TECHNOLOGY
    created_by = SubFactory(UserFactory)
    team = LazyAttribute(lambda o: o.created_by.team)

    class Meta:
        model = Client
