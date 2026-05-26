Status: ready-for-agent

# `generate_roadmap` AI service function

## Parent

[PRD: Roadmap Section](../PRD.md)

## What to build

Add a `generate_roadmap` function to the AI service that synthesizes all CategoryRecommendations and CategorySections into the structured Roadmap output. This is the only generation function in the codebase that requires `max_tokens=8192` — all others use 4096. It gets a dedicated LLM client rather than using the shared `_default_llm_client()`.

The function signature takes:
- `category_recommendations` — `dict[str, list[str]]` (category name → list of 7 recommendations), the same shape passed to `generate_recommendations_overview`
- `category_sections` — `dict[str, str]` (category name → assembled section text), using the existing `_build_section_text` helper
- `business_name` — `str`
- `llm_client` — injectable callable for testing (optional, defaults to the dedicated roadmap client)

It returns a dict with keys `months`, `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections`.

Use tool calling with a `record_roadmap` tool. The tool schema must enforce:
- `months`: array, `minItems: 12`, `maxItems: 12`; each object has `goals`, `action_items`, `challenges`, each an array with `minItems: 5`, `maxItems: 5`
- `potential_challenges`: array, `minItems: 4`, `maxItems: 7`
- `post_implementation_outcomes`: array, `minItems: 4`, `maxItems: 7`
- `closing_reflections`: array (no fixed count)

The prompt must:
- Instruct the model to write in third person, using the business name throughout
- Include all CategoryRecommendations and CategorySections as context
- Instruct month sequencing — early months address foundational areas, later months build on them
- Instruct that each month is comprehensive across all categories, though one category may be prioritised when it is a prerequisite
- Not pass scores as input (severity is already encoded in the CategorySection Path Forward content)
- Not accept prior roadmap content (always generated fresh)
- Not accept feedback text (no direct feedback path for Roadmap)

## Acceptance criteria

- [ ] `generate_roadmap` function exists in the AI service and accepts the inputs described above
- [ ] Uses tool calling (`tool_choice`) with a `record_roadmap` tool; schema enforces 12 months and 5 items per monthly sub-array
- [ ] Dedicated LLM client uses `max_tokens=8192`; the shared `_default_llm_client()` is not used for this call
- [ ] Unit test: given stub inputs and an injectable stub client, the return value is a dict with `months` (list of 12 items, each with `goals`, `action_items`, `challenges` lists of 5 strings), `potential_challenges` (non-empty list), `post_implementation_outcomes` (non-empty list), `closing_reflections` (non-empty list)
- [ ] Unit test: prompt contains the category recommendations text and category section text
- [ ] Unit test: prompt instructs third-person voice using the business name
- [ ] No raw numeric scores appear in the prompt or output

## Blocked by

None — can be developed in parallel with issue 01
