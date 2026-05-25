from decimal import Decimal

from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from complete_business_analysis_tool.assessments.models import (
    Answer,
    Assessment,
    AssessmentTemplate,
    Category,
    Question,
    QuestionOption,
)
from complete_business_analysis_tool.clients.factories import ClientFactory


class CategoryFactory(DjangoModelFactory[Category]):
    name = Faker("word")

    class Meta:
        model = Category


class AssessmentTemplateFactory(DjangoModelFactory[AssessmentTemplate]):
    title = Faker("sentence", nb_words=4)

    class Meta:
        model = AssessmentTemplate


class AssessmentFactory(DjangoModelFactory[Assessment]):
    template = SubFactory(AssessmentTemplateFactory)
    client = SubFactory(ClientFactory)

    class Meta:
        model = Assessment


class QuestionFactory(DjangoModelFactory[Question]):
    body = Faker("sentence")
    category = SubFactory(CategoryFactory)

    class Meta:
        model = Question


class QuestionOptionFactory(DjangoModelFactory[QuestionOption]):
    question = SubFactory(QuestionFactory)
    text = Faker("sentence", nb_words=3)
    rank = 1
    weight = Decimal("1.0000")

    class Meta:
        model = QuestionOption


class AnswerFactory(DjangoModelFactory[Answer]):
    assessment = SubFactory(AssessmentFactory)
    question = SubFactory(QuestionFactory)
    selected_option = SubFactory(
        QuestionOptionFactory,
        question=LazyAttribute(lambda o: o.factory_parent.question),
    )
    question_snapshot = LazyAttribute(lambda o: o.question.body)
    option_snapshot = LazyAttribute(
        lambda o: {"text": o.selected_option.text, "rank": o.selected_option.rank},
    )

    class Meta:
        model = Answer
