"""Management command to quickly generate a test client and assessment."""

from __future__ import annotations

import random
import sys

from django.core.management.base import BaseCommand
from django.db import transaction

from complete_business_analysis_tool.assessments.models import (
    Answer,
    Assessment,
    AssessmentTemplate,
    TemplateQuestion,
)
from complete_business_analysis_tool.clients.models import Client, IndustryType


def _pick_rank(rating: int, available_ranks: list[int]) -> int:
    """Select a QuestionOption rank from available_ranks using the 1-10 rating.

    Maps the 1-10 rating to a float centre in the 1-5 rank space, then adds
    Gaussian noise so individual questions within a category vary rather than
    all landing on the same rank.
    """
    centre = 1.0 + (rating - 1) * 4.0 / 9.0
    target = centre + random.gauss(0, 0.8)
    target = max(1.0, min(5.0, target))
    return min(available_ranks, key=lambda r: abs(r - target))


def _prompt(label: str, *, required: bool = True) -> str:
    while True:
        value = input(f"  {label}: ").strip()
        if value or not required:
            return value
        sys.stdout.write("  This field is required.\n")


def _prompt_choice(label: str, choices: list[tuple[str, str]]) -> str:
    """Display a numbered list of choices and return the selected value."""
    sys.stdout.write(f"\n  {label}:\n")
    for i, (_value, display) in enumerate(choices, 1):
        sys.stdout.write(f"    {i:2}. {display}\n")
    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1][0]
        sys.stdout.write(f"  Please enter a number between 1 and {len(choices)}.\n")


def _prompt_int(label: str, lo: int, hi: int) -> int:
    while True:
        raw = input(f"  {label} ({lo}-{hi}): ").strip()
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        sys.stdout.write(f"  Please enter a whole number between {lo} and {hi}.\n")


class Command(BaseCommand):
    help = "Interactively generate a test client and assessment for report testing."

    def handle(self, *args, **options):
        self.stdout.write("\n=== Generate Test Assessment ===\n")

        # --- Step 1: client info ---
        self.stdout.write("\n-- Client Information --")
        business_name = _prompt("Business name")
        first_name = _prompt("First name")
        last_name = _prompt("Last name")
        title = _prompt("Title / role")
        industry = _prompt_choice("Industry", IndustryType.choices)

        # --- Step 2: template selection ---
        templates = list(AssessmentTemplate.objects.order_by("title"))
        if not templates:
            self.stderr.write(
                "No assessment templates found. Run the seed script first.",
            )
            return

        self.stdout.write("\n-- Assessment Template --")
        template_choices = [(str(t.pk), t.title) for t in templates]
        template_pk = _prompt_choice("Select a template", template_choices)
        template = next(t for t in templates if str(t.pk) == template_pk)

        # --- Step 3: create client + assessment ---
        with transaction.atomic():
            client = Client.objects.create(
                business_name=business_name,
                first_name=first_name,
                last_name=last_name,
                title=title,
                industry=industry,
            )
            assessment = Assessment.objects.create(template=template, client=client)

            # --- Step 4: per-category ratings → answers ---
            template_questions = (
                TemplateQuestion.objects.filter(template=template)
                .select_related("question", "question__category")
                .prefetch_related("question__options")
                .order_by("order")
            )

            # Group by category while preserving template order
            groups: dict[str | None, list] = {}
            for tq in template_questions:
                cat_name = (
                    tq.question.category.name if tq.question.category else "General"
                )
                groups.setdefault(cat_name, []).append(tq)

            self.stdout.write(f"\n-- Category Ratings ({len(groups)} categories) --")
            answers_to_create: list[Answer] = []

            for cat_name, tqs in groups.items():
                rating = _prompt_int(f"Rating for '{cat_name}'", 1, 10)

                for tq in tqs:
                    question = tq.question
                    options = list(question.options.order_by("rank"))
                    if not options:
                        continue
                    available_ranks = [o.rank for o in options]
                    chosen_rank = _pick_rank(rating, available_ranks)
                    option = next(o for o in options if o.rank == chosen_rank)

                    answers_to_create.append(
                        Answer(
                            assessment=assessment,
                            question=question,
                            selected_option=option,
                            question_snapshot=question.body,
                            option_snapshot={
                                "id": str(option.pk),
                                "text": option.text,
                                "rank": option.rank,
                                "weight": str(option.weight),
                            },
                        ),
                    )

            Answer.objects.bulk_create(answers_to_create)

        # --- Step 5: summary ---
        self.stdout.write(self.style.SUCCESS("\n=== Done ==="))
        self.stdout.write(
            f"  Client:      {client.business_name} ({client.first_name} "
            f"{client.last_name})",
        )
        self.stdout.write(f"  Assessment:  {template.title}")
        self.stdout.write(f"  Answers:     {len(answers_to_create)}")
        self.stdout.write(f"  URL:         /assessments/{assessment.pk}/")
        self.stdout.write("")
