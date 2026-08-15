Status: complete

# Assessment lifecycle schema and completion readiness checker

## What to build

Foundational schema and pure logic that the rest of the Category Guidance feature depends on.

**`Assessment.status`** — CharField with choices `draft`, `in_progress`, `complete`. Defaults to `draft` on creation (existing `Assessment.objects.create(...)` call sites keep working unchanged since it's a default). No other code in this slice sets it to `in_progress` or `complete` yet — that happens in later slices.

**`Assessment.guidance_submitted_at`** — nullable `DateTimeField`. Not set by anything in this slice; later slices stamp it.

**`CategoryGuidance` model** — new model in the `assessments` app, same shape as `CategoryFeedback`. Fields: `assessment` FK (cascade delete, `related_name="category_guidance"`), `category` FK, `text` TextField. Register in Django admin.

**Migration + backfill** — a data migration that sets `status="complete"` and `guidance_submitted_at=created_at` for every existing `Assessment` row (all of which are fully answered under the pre-feature flow). No `CategoryGuidance` rows are created for existing assessments.

**Completion readiness checker** — a function (e.g. `assessments/services.py::assessment_completion_status(assessment)`) that takes an `Assessment` and returns whether it's eligible to be marked complete, plus which condition is unmet. Eligible requires both: `guidance_submitted_at is not None`, and every `Question` reachable from the assessment's `template` (via `TemplateQuestion`) has a corresponding `Answer` for this assessment. Pure function — no HTTP concerns, callable from a view without needing a request. Not wired into any view in this slice; that's for the Mark Complete slice.

## Acceptance criteria

- [x] `Assessment.status` field exists with choices `draft`/`in_progress`/`complete`, defaulting to `draft`
- [x] `Assessment.guidance_submitted_at` exists as a nullable `DateTimeField`
- [x] `CategoryGuidance` model exists with `assessment` FK (`related_name="category_guidance"`), `category` FK, `text` TextField, and is registered in Django admin
- [x] Migration applies cleanly and backfills every existing `Assessment` to `status="complete"`, `guidance_submitted_at=created_at`
- [x] Backfill migration creates no `CategoryGuidance` rows
- [x] `assessment_completion_status()` returns ineligible with a reason when `guidance_submitted_at` is null, regardless of answer completeness
- [x] `assessment_completion_status()` returns ineligible with a reason when one or more template questions have no `Answer`, regardless of `guidance_submitted_at`
- [x] `assessment_completion_status()` returns ineligible with both reasons when neither condition is met
- [x] `assessment_completion_status()` returns eligible when `guidance_submitted_at` is set and every template question has an `Answer`
- [x] Unit tests for the readiness checker use factories, no view/request involved

## Blocked by

None — can start immediately.
