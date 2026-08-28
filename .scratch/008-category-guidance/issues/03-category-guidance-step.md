Status: complete

# Category Guidance step

## What to build

A page where the advisor enters optional free-text guidance per Category, before or alongside answering Questions, to steer AI generation toward areas the standard Questions don't cover.

**`CategoryGuidanceForm`** — dynamically builds one optional `CharField`/`Textarea` per Category reachable from the assessment's template: `Category.objects.filter(questions__template_questions__template=assessment.template).distinct().order_by("name")`. This must work even when the Assessment has zero Answers yet (can't derive categories from answered questions, unlike existing `_assessment_categories` in the `reports` app). Pre-fill each field from any existing `CategoryGuidance.text` for that assessment+category, so revisiting the step shows what was already entered.

On save:
- For each category field with non-blank text: create or update the `CategoryGuidance` row for that assessment+category
- For each category field left blank where a `CategoryGuidance` row already exists (advisor cleared previously-entered text): delete that row
- Stamp `assessment.guidance_submitted_at = now()` regardless of how many fields were filled
- If `assessment.status == "draft"`, advance it to `"in_progress"`

**`CategoryGuidanceView`** — `FormView` (or `UpdateView`-style) scoped to an Assessment pk. Available regardless of current status, as long as status is not `complete` (once complete, the step is locked — reject with a message rather than 404, since the advisor may still navigate here from a stale link).

**Routing** — new URL scoped under the Assessment's pk (e.g. `assessments/<assessment_pk>/guidance/`). Not yet linked from anywhere in the UI — that wiring happens in the hub page slice. It's fine (and expected) for this slice to be reachable only by direct URL for now.

## Acceptance criteria

- [x] Guidance page lists exactly the categories reachable from the assessment's template, alphabetically, regardless of whether any questions have been answered
- [x] All fields are optional — submitting with everything blank succeeds
- [x] Submitting with some fields filled creates `CategoryGuidance` rows only for the non-blank ones
- [x] Resubmitting with revised text updates the existing row rather than creating a duplicate
- [x] Clearing a previously-filled field on resubmit deletes that `CategoryGuidance` row
- [x] `guidance_submitted_at` is stamped on every successful submit, including all-blank submissions
- [x] A `draft` Assessment advances to `in_progress` after a successful guidance submit
- [x] An `in_progress` Assessment stays `in_progress` (no regression) after a successful guidance submit
- [x] A `complete` Assessment rejects further guidance submissions with a clear message, no changes persisted
- [x] Revisiting the page pre-fills fields with previously entered text
- [x] View requires login, matching existing views
- [x] Tests cover: blank-skipping, update-in-place, deletion-on-clear, status advancement, and the locked-when-complete case

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs `CategoryGuidance` model and `guidance_submitted_at`
- `02-start-assessment.md` — needs a way to create a draft Assessment to attach guidance to

## Comments

Implemented as specified: `CategoryGuidanceForm`/`CategoryGuidanceView` added in `assessments/forms.py` and `assessments/views.py`, new `assessments:guidance` URL at `<uuid:pk>/guidance/`, new `assessment-guidance.html` template, `CategoryGuidanceFactory` added for tests. 21 tests added covering every acceptance criterion; full suite (228 tests), ruff, and mypy (no new errors vs. baseline) all green.

A multi-agent code review during implementation caught two real bugs beyond the spec, both fixed before commit:
- The original `dispatch()` override checked `assessment.status == complete` before `LoginRequiredMixin`'s auth check ran, letting an anonymous user hit the locked-assessment redirect without being sent to login. Fixed by moving the check into `get()`/`post()` (which only run after auth succeeds), with a regression test covering the anonymous+complete case specifically.
- The per-category create/update/delete loop plus the final `Assessment.save()` weren't wrapped in a transaction, unlike the sibling `AssessmentEntryForm.save()`. Wrapped `form_valid()` in `@transaction.atomic` for all-or-nothing persistence.

As in the spec, this step is reachable only by direct URL for now — no link exists yet from the Assessment detail (hub) page. That wiring is deferred to the hub page slice (`05-hub-page-and-mark-complete.md`), as intended.
