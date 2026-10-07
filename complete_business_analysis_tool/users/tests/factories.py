from __future__ import annotations

from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.teams.factories import TeamFactory
from complete_business_analysis_tool.users.models import User


class UserFactory(DjangoModelFactory[User]):
    """Produces a User with a Team; pass ``team=None`` for a User without one."""

    email = Faker("email")
    name = Faker("name")
    team = SubFactory(TeamFactory)

    @post_generation
    def password(self: User, create: bool, extracted: str | None, **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)
        if create:
            self.save()

    class Meta:
        model = User
        django_get_or_create = ["email"]
        skip_postgeneration_save = True
