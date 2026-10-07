from factory import Faker
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.teams.models import Team


class TeamFactory(DjangoModelFactory[Team]):
    name = Faker("company")

    class Meta:
        model = Team
