## Parent

[PRD: Roadmap Prose Fields — Array to TextField Migration](../PRD.md)

## What to build

Status: complete

Update the Roadmap LLM tool schema and generation prompt so that `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` are generated as flowing prose strings rather than arrays of one-sentence items.

In the `_ROADMAP_TOOL` schema definition, change the three fields from `array of string` to `string`. Remove the `minItems`/`maxItems` constraints — paragraph count is enforced through prompt instructions instead.

Update the roadmap generation prompt to instruct the model to write:
- Potential Challenges as 3–4 prose paragraphs
- Post-Implementation Outcomes as 3–4 prose paragraphs
- Closing Reflections as 4–6 prose paragraphs

All three must use `\n\n` to separate paragraphs, with no bullet points or list formatting.

Update `test_roadmap_ai_service.py` stubs to return strings for these three fields. Update `test_lifecycle.py` stubs and assertions accordingly.

## Acceptance criteria

- [x] The `_ROADMAP_TOOL` schema defines `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` as `{"type": "string"}`
- [x] The roadmap generation prompt specifies 3–4 paragraphs for Potential Challenges, 3–4 for Post-Implementation Outcomes, and 4–6 for Closing Reflections, with `\n\n` as the paragraph separator
- [x] The prompt explicitly instructs the model not to use bullet points or list formatting in these three fields
- [x] `test_roadmap_ai_service.py` LLM stub returns strings (with `\n\n` separators) for the three fields; tests pass
- [x] `test_lifecycle.py` stubs and assertions are updated; tests pass
- [x] The Roadmap generation task successfully persists the string values returned by the LLM to the `TextField` columns

## Blocked by

- [01 — Migrate Roadmap prose fields from JSONField to TextField](01-migrate-roadmap-prose-fields.md)
