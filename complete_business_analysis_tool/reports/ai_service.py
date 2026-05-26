from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic
from django.conf import settings

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal


def generate_executive_summary(  # noqa: PLR0913
    category_sections: dict[str, str],
    category_scores: dict[str, Decimal],
    category_max_scores: dict[str, Decimal],
    business_name: str,
    prior_content: str | None = None,
    feedback_text: str | None = None,
    llm_client: Callable[[str], str] | None = None,
) -> str:
    if llm_client is None:
        llm_client = _default_llm_client()
    prompt = _build_overall_prompt(
        category_sections,
        category_scores,
        category_max_scores,
        business_name,
        prior_content,
        feedback_text,
    )
    return llm_client(prompt)


def generate_category_section(  # noqa: PLR0913
    answers: list[dict],
    business_name: str,
    prior_overview: str | None = None,
    prior_impact: str | None = None,
    prior_path_forward: str | None = None,
    feedback_text: str | None = None,
    llm_client: Callable[[str], dict] | None = None,
) -> dict:
    if llm_client is None:
        llm_client = _default_category_section_client()
    prompt = _build_category_prompt(
        answers,
        business_name,
        prior_overview,
        prior_impact,
        prior_path_forward,
        feedback_text,
    )
    return llm_client(prompt)


def _build_category_prompt(  # noqa: PLR0913
    answers: list[dict],
    business_name: str,
    prior_overview: str | None = None,
    prior_impact: str | None = None,
    prior_path_forward: str | None = None,
    feedback_text: str | None = None,
) -> str:
    lines = [
        "You are a business advisor writing a section of a business analysis report.",
        f"Write in third person, referring to the business as {business_name}."
        f" Use {business_name} instead of 'you' or 'your'.",
        "",
        "Assessment answers:",
    ]
    for answer in answers:
        question = answer["question_snapshot"]
        option = answer["option_snapshot"]
        option_text = option.get("text", "") if isinstance(option, dict) else str(option)
        lines.append(f"  Q: {question}")
        lines.append(f"  A: {option_text}")

    if prior_overview:
        lines.append("")
        lines.append(f"Current Overview sub-section to revise:\n{prior_overview}")

    if prior_impact:
        lines.append("")
        lines.append(f"Current Impact sub-section to revise:\n{prior_impact}")

    if prior_path_forward:
        lines.append("")
        lines.append(f"Current Path Forward sub-section to revise:\n{prior_path_forward}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write three sections:",
            "  overview — current state of this business area (5-8 sentences, "
            "third person)",
            "  impact — how the current state affects the business (5-8 sentences, "
            "third person)",
            "  path_forward — changes needed to improve (5-8 sentences, third person)",
        ],
    )
    return "\n".join(lines)


def _build_overall_prompt(  # noqa: PLR0913
    category_sections: dict[str, str],
    category_scores: dict[str, Decimal],
    category_max_scores: dict[str, Decimal],
    business_name: str,
    prior_content: str | None = None,
    feedback_text: str | None = None,
) -> str:
    lines = [
        "You are a business advisor writing the Overall section of a business "
        "analysis report.",
        f"Write in third person, referring to the business as {business_name}."
        f" Use {business_name} instead of 'you' or 'your'.",
        "",
        "Internal context — category scores (do not cite raw numeric scores in "
        "your output):",
    ]
    for category, score in category_scores.items():
        max_score = category_max_scores.get(category, score)
        lines.append(f"  - {category}: {score} / {max_score}")

    lines.append("")
    lines.append("Category sections:")
    for category, section_text in category_sections.items():
        lines.append(f"\n## {category}\n{section_text}")

    if prior_content:
        lines.append("")
        lines.append(f"Current Overall section to revise:\n{prior_content}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write the Executive Summary in 4-5 paragraphs. Weave the category sections"
            " above into a coherent, holistic picture of the business. Focus on synthesis"
            " only — the individual category sections already cover what to act on and"
            " when. Write entirely in third person, referring to the business "
            f"as {business_name}.",
        ],
    )
    return "\n".join(lines)


_CATEGORY_SECTION_TOOL: dict = {
    "name": "record_category_section",
    "description": "Record the structured analysis for this business category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "overview": {
                "type": "string",
                "description": "Current state of this business area (5-8 "
                "sentences, third person).",
            },
            "impact": {
                "type": "string",
                "description": "How the current state affects the business (5-8 "
                "sentences, third person).",
            },
            "path_forward": {
                "type": "string",
                "description": "Changes needed to improve (5-8 sentences, third person).",
            },
        },
        "required": ["overview", "impact", "path_forward"],
    },
}


def _default_category_section_client() -> Callable[[str], dict]:
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

    def call(prompt: str) -> dict:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            tools=[_CATEGORY_SECTION_TOOL],
            tool_choice={"type": "tool", "name": "record_category_section"},
        )
        return message.content[0].input

    return call


def _default_llm_client() -> Callable[[str], str]:

    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

    def call(prompt: str) -> str:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    return call
