"""Forms for the assessments application."""

from __future__ import annotations

from django import forms
from django.db import transaction

from complete_business_analysis_tool.clients.models import Client

from .models import Answer, Assessment, AssessmentTemplate, QuestionOption
from .widgets import RankedRadioSelect


class AssessmentEntryForm(forms.Form):
    """Dynamically built form for completing an assessment.

    Fields are generated at init time from the template's ordered questions.
    Field names use the pattern ``question_<pk_hex>`` to avoid UUID hyphens,
    which are invalid in Python identifiers and problematic in HTML name attrs.
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

        self.template_questions = (
            template.template_questions.select_related(
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
        """Create and return an Assessment with one Answer per question.

        Must only be called after is_valid() returns True.
        """
        client = self.cleaned_data["client"]
        assessment = Assessment.objects.create(template=self.template, client=client)

        option_cache: dict[str, QuestionOption] = {}
        for tq in self.template_questions:
            q = tq.question
            opt_pk = self.cleaned_data[f"question_{q.pk.hex}"]
            if opt_pk not in option_cache:
                option_cache[opt_pk] = QuestionOption.objects.get(pk=opt_pk)
            opt = option_cache[opt_pk]

            Answer.objects.create(
                assessment=assessment,
                question=q,
                selected_option=opt,
                question_snapshot=q.body,
                option_snapshot={
                    "id": str(opt.pk),
                    "text": opt.text,
                    "rank": opt.rank,
                    "weight": str(opt.weight),  # Decimal is not JSON-serializable
                },
            )

        return assessment
