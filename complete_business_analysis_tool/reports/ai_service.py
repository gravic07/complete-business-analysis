from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic
from django.conf import settings

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal


def generate_section(  # noqa: PLR0913
    scope_label: str,
    answers: list[dict],
    category_scores: dict[str, Decimal],
    total_score: Decimal,
    feedback_text: str | None = None,
    prior_content: str | None = None,
    llm_client: Callable[[str], str] | None = None,
) -> str:
    if llm_client is None:
        llm_client = _default_llm_client()
    prompt = _build_prompt(
        scope_label,
        answers,
        category_scores,
        total_score,
        feedback_text,
        prior_content,
    )
    return llm_client(prompt)


def generate_category_section(
    answers: list[dict],
    prior_content: str | None = None,
    feedback_text: str | None = None,
    llm_client: Callable[[str], str] | None = None,
) -> str:
    if llm_client is None:
        llm_client = _default_llm_client()
    prompt = _build_category_prompt(answers, prior_content, feedback_text)
    return llm_client(prompt)


def _build_category_prompt(
    answers: list[dict],
    prior_content: str | None = None,
    feedback_text: str | None = None,
) -> str:
    lines = [
        "You are a business advisor writing a section of a business analysis report.",
        "Write in second person, addressing the client directly"
        " (use 'your business', 'you are currently', etc.).",
        "",
        "Assessment answers:",
    ]
    for answer in answers:
        question = answer["question_snapshot"]
        option = answer["option_snapshot"]
        option_text = (
            option.get("text", "") if isinstance(option, dict) else str(option)
        )
        lines.append(f"  Q: {question}")
        lines.append(f"  A: {option_text}")

    if prior_content:
        lines.append("")
        lines.append(f"Current section content to revise:\n{prior_content}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write a concise, actionable narrative (2-4 paragraphs) for this section "
            "of the business analysis report. Focus on the client's current strengths, "
            "weaknesses, and specific recommendations.",
        ],
    )
    return "\n".join(lines)


def _build_prompt(  # noqa: PLR0913
    scope_label: str,
    answers: list[dict],
    category_scores: dict[str, Decimal],
    total_score: Decimal,
    feedback_text: str | None,
    prior_content: str | None = None,
) -> str:
    lines = [
        "You are a business advisor writing a section of a business analysis report.",
        "",
        f"Section: {scope_label}",
        f"Overall business score: {total_score}",
    ]

    if category_scores:
        lines.append("Category scores:")
        for category, score in category_scores.items():
            lines.append(f"  - {category}: {score}")

    if answers:
        lines.append("")
        lines.append("Assessment answers:")
        for answer in answers:
            question = answer["question_snapshot"]
            option = answer["option_snapshot"]
            option_text = (
                option.get("text", "") if isinstance(option, dict) else str(option)
            )
            lines.append(f"  Q: {question}")
            lines.append(f"  A: {option_text}")

    if prior_content:
        lines.append("")
        lines.append(f"Current section content to revise:\n{prior_content}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write a concise, actionable narrative (2-4 paragraphs) for this section "
            "of the business analysis report. Focus on the client's current strengths, "
            "weaknesses, and specific recommendations.",
        ],
    )

    return "\n".join(lines)


def _default_llm_client() -> Callable[[str], str]:

    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

    def call(prompt: str) -> str:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    return call
