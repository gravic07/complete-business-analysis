"""Forms for the assessments application."""

from __future__ import annotations

from django import forms
from django.db import transaction

from complete_business_analysis_tool.clients.models import Client

from .models import Answer, Assessment, AssessmentTemplate, Category, QuestionOption
from .widgets import RankedRadioSelect


class AssessmentStartForm(forms.Form):
    """Minimal form for creating a draft Assessment from a client selection.

    The template is fixed at construction time (from the URL); this form only
    collects the client.
    """

    client = forms.ModelChoiceField(
        queryset=None,
        label="Client",
        empty_label="-- Select a client --",
        widget=forms.Select(attrs={"class": "input"}),
    )

    def __init__(self, *args, template: AssessmentTemplate, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template
        self.fields["client"].queryset = Client.objects.order_by("business_name")

    def save(self) -> Assessment:
        """Create and return a draft Assessment for the chosen client."""
        return Assessment.objects.create(
            template=self.template,
            client=self.cleaned_data["client"],
        )


class AssessmentAnswerForm(forms.Form):
    """Dynamically built form for answering an existing assessment's questions.

    Fields are generated at init time from the assessment template's ordered
    questions. Field names use the pattern ``question_<pk_hex>`` to avoid UUID
    hyphens, which are invalid in Python identifiers and problematic in HTML
    name attrs.
    """

    def __init__(self, *args, assessment: Assessment, **kwargs):
        super().__init__(*args, **kwargs)

        self.assessment = assessment
        self.template = assessment.template

        self.template_questions = (
            self.template.template_questions.select_related(
                "question",
                "question__category",
            )
            .prefetch_related("question__options")
            .order_by("order")
        )

        for tq in self.template_questions:
            q = tq.question
            field_name = f"question_{q.pk.hex}"
            options = list(q.options.order_by("-rank"))
            choices = [(str(opt.pk), opt.text) for opt in options]
            option_ranks = {str(opt.pk): opt.rank for opt in options}
            self.fields[field_name] = forms.ChoiceField(
                label=q.body,
                choices=choices,
                widget=RankedRadioSelect(option_ranks=option_ranks),
                required=True,
            )

    def get_grouped_fields(self) -> list[tuple[str | None, list]]:
        """Return questions grouped by category for template rendering.

        Returns a list of (category_name_or_None, [bound_field, ...]) pairs,
        preserving the TemplateQuestion order within each category.
        """
        groups: dict[str | None, list] = {}
        for tq in self.template_questions:
            q = tq.question
            cat_name = q.category.name if q.category else None
            groups.setdefault(cat_name, []).append(self[f"question_{q.pk.hex}"])
        return list(groups.items())

    @transaction.atomic
    def save(self) -> Assessment:
        """Create or update one Answer per question on the existing Assessment.

        Resubmitting updates the existing Answer for a question in place
        (rather than erroring on the assessment/question unique_together
        constraint). Advances a draft Assessment to in_progress.

        Must only be called after is_valid() returns True.
        """
        option_cache: dict[str, QuestionOption] = {}
        for tq in self.template_questions:
            q = tq.question
            opt_pk = self.cleaned_data[f"question_{q.pk.hex}"]
            if opt_pk not in option_cache:
                option_cache[opt_pk] = QuestionOption.objects.get(pk=opt_pk)
            opt = option_cache[opt_pk]

            Answer.objects.update_or_create(
                assessment=self.assessment,
                question=q,
                defaults={
                    "selected_option": opt,
                    "question_snapshot": q.body,
                    "option_snapshot": {
                        "id": str(opt.pk),
                        "text": opt.text,
                        "rank": opt.rank,
                        "weight": str(opt.weight),  # Decimal is not JSON-serializable
                    },
                },
            )

        if self.assessment.status == Assessment.Status.DRAFT:
            self.assessment.status = Assessment.Status.IN_PROGRESS
            self.assessment.save(update_fields=["status"])

        return self.assessment


class CategoryGuidanceForm(forms.Form):
    """Dynamically built form with one optional text field per Category.

    Field names use the pattern ``category_<pk_hex>`` to avoid UUID hyphens,
    which are invalid in Python identifiers and problematic in HTML name attrs.
    """

    def __init__(self, *args, categories, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = list(categories)
        for category in self.categories:
            self.fields[f"category_{category.pk.hex}"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 3, "class": "textarea"}),
                label=category.name,
            )

    def get_category_fields(self) -> list[tuple[Category, object]]:
        """Return (category, bound_field) pairs for template rendering."""
        return [
            (category, self[f"category_{category.pk.hex}"])
            for category in self.categories
        ]
