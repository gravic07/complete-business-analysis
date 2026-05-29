# PRD: Roadmap Prose Fields — Array to TextField Migration

Status: ready-for-agent

## Problem Statement

The three closing sections of the Roadmap — Potential Challenges, Post-Implementation Outcomes, and Closing Reflections — are stored as arrays of strings and generated via a JSON schema that defines them as `array of string`. This schema type signals "list of discrete items" to the LLM, causing it to produce one-sentence, bullet-point-style content per array element rather than flowing multi-sentence paragraphs. The report template compounds the problem by iterating over the array and wrapping each element in a `<p>` tag, which surfaces the terse, fragmented content directly to the reader. The result is three sections that read as bullet lists rather than coherent prose.

## Solution

Change the three fields (`potential_challenges`, `post_implementation_outcomes`, `closing_reflections`) from `JSONField (array of strings)` to `TextField (plain string)` in both the Django model and the LLM tool schema. Update the roadmap generation prompt to specify paragraph counts and instruct the model to separate paragraphs with `\n\n`. Update the report template to render the stored string using the `|linebreaks` filter, which converts double newlines to `<p>` tags. Update all tests to reflect the new string-based format.

Paragraph targets per the updated domain model:
- **Potential Challenges** — 3–4 paragraphs
- **Post-Implementation Outcomes** — 3–4 paragraphs
- **Closing Reflections** — 4–6 paragraphs

## User Stories

1. As a Client reading the Report, I want the Potential Challenges section to read as coherent prose paragraphs, so that I can understand the implementation obstacles as a connected narrative rather than a fragmented list.
2. As a Client reading the Report, I want the Post-Implementation Outcomes section to read as flowing paragraphs that connect each addressed weakness to an improved business outcome, so that I can visualise the full picture of what success looks like.
3. As a Client reading the Report, I want the Closing Reflections section to read as an encouraging, paragraph-structured close, so that I leave the report with clear, actionable motivation rather than disconnected bullet points.
4. As an Advisor reviewing the Report before delivery, I want the three closing sections to present polished, consultant-quality prose, so that I can deliver the report to the Client with confidence.
5. As an Advisor, I want the paragraph counts to be appropriately scoped (3–4 for challenges and outcomes, 4–6 for closing reflections), so that these sections are thorough without being padded.
6. As a developer generating a Roadmap, I want the LLM tool schema to specify `string` for these three fields, so that the model's generative defaults align with the desired prose output rather than working against it.
7. As a developer maintaining the codebase, I want these fields stored as `TextField` rather than `JSONField`, so that the storage type reflects the content type and no unnecessary JSON parsing occurs.
8. As a developer running tests, I want all test fixtures and mocks for Roadmap to use `\n\n`-separated strings for these three fields, so that test data accurately reflects production data shape.

## Implementation Decisions

- **Django model change**: `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` on the `Roadmap` model are changed from `JSONField` to `TextField`. No default value is needed — these fields are always populated at creation by the LLM generation task.

- **LLM tool schema change**: In the `_ROADMAP_TOOL` definition in `ai_service.py`, the three array schemas are replaced with `{"type": "string"}`. The `minItems`/`maxItems` constraints are dropped — paragraph count is enforced through prompt instructions instead.

- **Prompt instruction update**: The roadmap generation prompt is updated to instruct the model to write Potential Challenges as 3–4 paragraphs, Post-Implementation Outcomes as 3–4 paragraphs, and Closing Reflections as 4–6 paragraphs, with paragraphs separated by `\n\n` and no bullet points or list formatting.

- **Template rendering**: The `{% for item in roadmap.potential_challenges %}` pattern in `report-detail.html` is replaced with `{{ roadmap.potential_challenges|linebreaks }}` (and equivalently for the other two fields). Django's `linebreaks` filter converts `\n\n` into `<p>` tags natively.

- **Django migration**: A new migration alters the three fields from `JSONField` to `TextField`. No data migration is required — no production data exists.

- **Test data shape**: All test fixtures, conftest stubs, and mock return values that previously set these fields to arrays of strings are updated to single `\n\n`-separated strings with paragraph content appropriate to the test scenario.

- **No serializer changes needed**: The Roadmap model is not exposed via a REST API — it is accessed only through the view/template layer.

- **No admin changes needed**: The admin registers these fields as `readonly_fields`, which renders correctly for both JSONField and TextField.

## Testing Decisions

A good test for this area verifies the **external behaviour visible to the reader** — that the rendered HTML contains paragraph-wrapped prose — not internal implementation details like field types or prompt text.

**Modules to test:**

- **Roadmap model** (`test_roadmap_model.py`): Verify that the model accepts a plain string with `\n\n` separators and stores/retrieves it correctly. Existing array-based fixtures must be updated to strings.

- **Roadmap AI service** (`test_roadmap_ai_service.py`): Verify that `generate_roadmap()` returns a dict with string values for the three prose fields when given a stubbed LLM response. The LLM stub must return strings, not arrays.

- **Report view** (`test_report_view.py`): Verify that the rendered report HTML contains `<p>` tags wrapping the prose content for Potential Challenges, Post-Implementation Outcomes, and Closing Reflections. This is the key external-behaviour test — it covers the full pipeline from stored value through template rendering.

- **Analysis lifecycle** (`test_lifecycle.py`): Fixtures in `conftest.py` that stub roadmap LLM responses must be updated to return strings. The lifecycle test itself may not need assertion changes if it only checks that the Roadmap object was created.

Prior art: the existing `test_report_view.py` already checks for rendered content in the HTML response — the same pattern applies here, updated for string content.

## Out of Scope

- Changes to the `months` field or any per-month sub-fields (`goals`, `action_items`, `challenges`) — these remain as `JSONField` arrays of strings and are not affected.
- Changes to the `overview` field on the Roadmap — static template content, not LLM-generated.
- Changes to any other Report sections (CategorySection, ExecutiveSummary, Recommendations) — their array-vs-string storage decisions are separate concerns.
- Backfilling or migrating any existing Roadmap records — confirmed no production data exists.
- API exposure of the Roadmap model — no REST serializer exists and none is planned.

## Further Notes

The root cause is a schema-driven content quality issue: the LLM model treats `array of string` as a signal to generate discrete, list-style items. Switching to `string` removes that signal entirely, producing prose-first output without requiring heavy prompt engineering. The paragraph count guidance in the prompt serves as the structural constraint instead.

The `CONTEXT.md` glossary has been updated to reflect the new paragraph counts and `TextField` storage for these three fields.
