from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic
from django.conf import settings

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal


RECOMMENDATION_STRENGTH_THRESHOLD = 0.75
RECOMMENDATION_MODERATE_THRESHOLD = 0.5


def generate_category_recommendations(  # noqa: PLR0913
    answers: list[dict],
    section_text: str,
    score: Decimal,
    max_score: Decimal,
    business_name: str,
    prior_recommendations: list[str] | None = None,
    feedback_text: str | None = None,
    llm_client: Callable[[str], list] | None = None,
) -> list[str]:
    if llm_client is None:
        llm_client = _default_category_recommendations_client()
    prompt = _build_category_recommendations_prompt(
        answers,
        section_text,
        score,
        max_score,
        business_name,
        prior_recommendations,
        feedback_text,
    )
    return llm_client(prompt)


def generate_recommendations_overview(  # noqa: PLR0913
    category_recommendations: dict[str, list[str]],
    category_scores: dict[str, Decimal],
    category_max_scores: dict[str, Decimal],
    business_name: str,
    prior_content: str | None = None,
    feedback_text: str | None = None,
    llm_client: Callable[[str], str] | None = None,
) -> str:
    if llm_client is None:
        llm_client = _default_llm_client()
    prompt = _build_recommendations_overview_prompt(
        category_recommendations,
        category_scores,
        category_max_scores,
        business_name,
        prior_content,
        feedback_text,
    )
    return llm_client(prompt)


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


def _build_recommendations_overview_prompt(  # noqa: PLR0913
    category_recommendations: dict[str, list[str]],
    category_scores: dict[str, Decimal],
    category_max_scores: dict[str, Decimal],
    business_name: str,
    prior_content: str | None = None,
    feedback_text: str | None = None,
) -> str:
    lines = [
        "You are a business advisor writing the Recommendations Overview section of a"
        " business analysis report.",
        f"Write in third person, referring to the business as {business_name}."
        f" Use {business_name} instead of 'you' or 'your'.",
        "",
        "Internal context — category scores (do not cite raw numeric scores in"
        " your output):",
    ]
    for category, score in category_scores.items():
        max_score = category_max_scores.get(category, score)
        lines.append(f"  - {category}: {score} / {max_score}")

    lines.append("")
    lines.append("Category recommendations:")
    for category, recs in category_recommendations.items():
        lines.append(f"\n## {category}")
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")

    if prior_content:
        lines.append("")
        lines.append(f"Current Recommendations Overview to revise:\n{prior_content}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write the Recommendations Overview in approximately 300-500 words."
            " Orient the client to where the biggest gaps are and what the"
            f" recommendations collectively aim to address. Be prescriptive and"
            " forward-looking — this section should motivate action, not analyse."
            " Write entirely in third person, referring to the business "
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


def _build_category_recommendations_prompt(  # noqa: PLR0913
    answers: list[dict],
    section_text: str,
    score: Decimal,
    max_score: Decimal,
    business_name: str,
    prior_recommendations: list[str] | None = None,
    feedback_text: str | None = None,
) -> str:
    ratio = float(score) / float(max_score) if max_score else 0.0
    if ratio >= RECOMMENDATION_STRENGTH_THRESHOLD:
        weight_guidance = (
            "This category is a strength. Weight the recommendations toward"
            " continuation — emphasize what to keep doing and build on."
        )
    elif ratio >= RECOMMENDATION_MODERATE_THRESHOLD:
        weight_guidance = (
            "This category is performing at a moderate level. Balance the"
            " recommendations evenly across what to start, stop, and continue."
        )
    else:
        weight_guidance = (
            "This category needs significant improvement. Weight the recommendations"
            " toward change — emphasize what to start and what to stop."
        )

    lines = [
        "You are a business advisor writing recommendations for a section of a"
        " business analysis report.",
        f"Write in third person, referring to the business as {business_name}."
        f" Use {business_name} instead of 'you' or 'your'.",
        "",
        "Internal context — category performance signal (do not cite raw numeric"
        " scores in your output):",
        f"  {weight_guidance}",
        "",
        "Analysis section for this category:",
        section_text,
        "",
        "Assessment answers for this category:",
    ]
    for answer in answers:
        question = answer["question_snapshot"]
        option = answer["option_snapshot"]
        option_text = option.get("text", "") if isinstance(option, dict) else str(option)
        lines.append(f"  Q: {question}")
        lines.append(f"  A: {option_text}")

    if prior_recommendations:
        lines.append("")
        lines.append("Prior recommendations to revise:")
        for i, rec in enumerate(prior_recommendations, 1):
            lines.append(f"  {i}. {rec}")

    if feedback_text:
        lines.append("")
        lines.append(f"Advisor feedback to incorporate: {feedback_text}")

    lines.extend(
        [
            "",
            "Write exactly 7 specific, actionable recommendations for this category."
            " Each recommendation should be 1-3 complete sentences. Consider what"
            f" {business_name} should start doing, stop doing, and continue doing —"
            " with the balance weighted as indicated above — but do not label"
            " individual recommendations as start/stop/continue.",
        ],
    )
    return "\n".join(lines)


_CATEGORY_RECOMMENDATIONS_TOOL: dict = {
    "name": "record_category_recommendations",
    "description": "Record the 7 actionable recommendations for this business category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 7,
                "maxItems": 7,
                "description": "Exactly 7 actionable recommendations.",
            },
        },
        "required": ["recommendations"],
    },
}


def _default_category_recommendations_client() -> Callable[[str], list]:
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

    def call(prompt: str) -> list:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            tools=[_CATEGORY_RECOMMENDATIONS_TOOL],
            tool_choice={"type": "tool", "name": "record_category_recommendations"},
        )
        return message.content[0].input["recommendations"]

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


_ROADMAP_TOOL = {
    "name": "record_roadmap",
    "description": "Record the structured 12-month roadmap.",
    "input_schema": {
        "type": "object",
        "properties": {
            "months": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "properties": {
                        "goals": {
                            "type": "array",
                            "minItems": 5,
                            "maxItems": 5,
                            "items": {"type": "string"},
                        },
                        "action_items": {
                            "type": "array",
                            "minItems": 5,
                            "maxItems": 5,
                            "items": {"type": "string"},
                        },
                        "challenges": {
                            "type": "array",
                            "minItems": 5,
                            "maxItems": 5,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["goals", "action_items", "challenges"],
                },
            },
            "potential_challenges": {"type": "string"},
            "post_implementation_outcomes": {"type": "string"},
            "closing_reflections": {"type": "string"},
        },
        "required": [
            "months",
            "potential_challenges",
            "post_implementation_outcomes",
            "closing_reflections",
        ],
    },
}


def _default_roadmap_client() -> Callable[[str], dict]:
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

    def call(prompt: str) -> dict:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
            tools=[_ROADMAP_TOOL],
            tool_choice={"type": "tool", "name": "record_roadmap"},
        )
        return message.content[0].input

    return call


def _build_roadmap_prompt(
    category_recommendations: dict[str, list[str]],
    category_sections: dict[str, str],
    business_name: str,
) -> str:
    lines = [
        f"You are writing a 12-month implementation roadmap for {business_name}.",
        f"Write in third person, referring to the business as {business_name} "
        "throughout.",
        "",
        "Use the following category assessments and recommendations as context.",
        "Do not include raw numeric scores anywhere in your response.",
        "Severity and priority are already encoded in the Path Forward content below.",
        "",
        "Early months should address foundational areas; later months build on them.",
        "Each month must be comprehensive across all categories, though one category",
        "may be prioritized when it is a prerequisite for others.",
        "",
        "For the three prose fields, write flowing narrative — no bullet points or list",
        "formatting of any kind. Separate paragraphs with \\n\\n.",
        "- potential_challenges: 3-4 paragraphs",
        "- post_implementation_outcomes: 3-4 paragraphs",
        "- closing_reflections: 4-6 paragraphs",
        "",
        "## Category Recommendations",
    ]
    for category, recommendations in category_recommendations.items():
        lines.append(f"\n### {category}")
        lines.extend(f"- {rec}" for rec in recommendations)

    lines.append("\n## Category Sections")
    for category, section_text in category_sections.items():
        lines.append(f"\n### {category}")
        lines.append(section_text)

    return "\n".join(lines)


def generate_roadmap(
    category_recommendations: dict[str, list[str]],
    category_sections: dict[str, str],
    business_name: str,
    llm_client: Callable[[str], dict] | None = None,
) -> dict:
    if llm_client is None:
        llm_client = _default_roadmap_client()
    prompt = _build_roadmap_prompt(
        category_recommendations,
        category_sections,
        business_name,
    )
    return llm_client(prompt)
