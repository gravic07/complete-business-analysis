## Parent

[PRD: Roadmap Prose Fields — Array to TextField Migration](../PRD.md)

## What to build

Status: complete

Change the three Roadmap prose fields — `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` — from `JSONField` to `TextField` on the Django `Roadmap` model. Create the corresponding migration. Update all model-layer test fixtures and assertions to use `\n\n`-separated strings instead of arrays of strings.

The field values are always written by the LLM generation task at Roadmap creation time and are never null — no default value is needed on the fields.

## Acceptance criteria

- [x] `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` are defined as `TextField` on the `Roadmap` model
- [x] A Django migration exists that alters the three fields from `JSONField` to `TextField`
- [x] `test_roadmap_model.py` fixtures and assertions use plain strings (with `\n\n` paragraph separators where multiple paragraphs are needed) instead of arrays
- [x] `analysis/tests/conftest.py` roadmap stub values for these three fields are updated to strings
- [x] All existing tests pass with the updated field types

## Blocked by

None — can start immediately
