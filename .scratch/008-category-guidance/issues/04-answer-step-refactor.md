Status: complete

# Answer step: attach Questions to an existing Assessment, retire AssessmentEntryView

## What to build

Extract today's question-answering logic out of `AssessmentEntryForm`/`AssessmentEntryView` into its own step that operates against an already-existing `Assessment` (created by the Start step) instead of creating one.

**`AssessmentAnswerForm`** — same dynamic per-question field-building as today's `AssessmentEntryForm` (one `ChoiceField` per template question, `RankedRadioSelect` widget, grouped-by-category rendering via the same `get_grouped_fields()` pattern), minus the `client` field. Takes an existing `assessment` instead of a `template` at construction (template is `assessment.template`). `save()` creates one `Answer` per question with the same snapshot behavior as today (`question_snapshot`, `option_snapshot`), still requiring every question to be answered in a single submission — no partial/incremental save in this slice. If an `Answer` already exists for a question on this assessment (advisor is resubmitting), update it in place rather than erroring on the `unique_together` constraint. After a successful save, if `assessment.status == "draft"`, advance it to `"in_progress"`.

**`AssessmentAnswerView`** — `FormView` scoped to an Assessment pk, replacing `AssessmentEntryView`'s question-answering responsibility. Pre-fills already-answered questions so revisiting the step (e.g. to fix an answer before Mark Complete) shows current selections. Rejects submission with a clear message if `assessment.status == "complete"` (locked, same posture as the Guidance step).

**Retire `AssessmentEntryView`/`AssessmentEntryForm`** — once this view covers the same ground (minus client selection, now handled by `AssessmentStartView`), remove the old view, form, URL, and its now-unused template content. No dual-path support needed — this repo has no external consumers of the old entry URL besides its own templates, which are updated in this slice.

**Routing** — new URL scoped under the Assessment's pk (e.g. `assessments/<assessment_pk>/answer/`). Not yet linked from the hub page — that's the next slice. Reachable by direct URL for now.

## Acceptance criteria

- [x] Answer page renders one field per template question, grouped by category, matching today's `AssessmentEntryForm` rendering
- [x] Submitting all questions creates one `Answer` per question with correct snapshots, against the existing Assessment (no new Assessment created)
- [x] Submitting with a question left unanswered fails validation, same as today
- [x] Resubmitting (e.g. advisor changes an answer before completing) updates the existing `Answer` rather than erroring or duplicating
- [x] A `draft` Assessment advances to `in_progress` after a successful answer submit
- [x] An `in_progress` Assessment stays `in_progress` (no regression) after a successful answer submit
- [x] A `complete` Assessment rejects further answer submissions with a clear message, no changes persisted
- [x] Revisiting the page pre-fills already-selected answers
- [x] `AssessmentEntryView`, `AssessmentEntryForm`, and the old entry URL/template are removed
- [x] No remaining references to the old entry URL name in templates or tests
- [x] Tests cover: full submit, partial submit rejection, resubmit/update, status advancement, and the locked-when-complete case

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs `Assessment.status`
- `02-start-assessment.md` — needs a way to create a draft Assessment to answer against, and needs to have taken over client selection before the old entry view can be safely removed

## Comments

Implemented as specified: `AssessmentAnswerForm`/`AssessmentAnswerView` added in `assessments/forms.py` and `assessments/views.py`, replacing `AssessmentEntryForm`/`AssessmentEntryView` (deleted). New `assessments:answer` URL at `<uuid:pk>/answer/` (assessment-scoped, replacing the template-scoped `<uuid:pk>/entry/`), new `assessment-answer.html` template (replacing `assessment-entry.html`, dropping the client-selection box and "Create Client" modal now owned by the Start step). 15 tests added covering every acceptance criterion; full suite (240 tests), and mypy (no new error categories vs. baseline) all green. A repo-wide grep confirmed no remaining references to `assessments:entry`, `AssessmentEntryView`, `AssessmentEntryForm`, or `assessment-entry.html` outside the intentional negative-check test.

`AssessmentAnswerForm.save()` uses `Answer.objects.update_or_create(assessment=..., question=..., defaults={...})` per question so a resubmit updates the existing row in place rather than hitting the `unique_together = [["assessment", "question"]]` constraint — mirrors the `update_or_create` pattern already used by `CategoryGuidanceForm`/`CategoryGuidanceView`. `AssessmentAnswerView` replicates `CategoryGuidanceView`'s `_reject_if_complete()` / `get()`/`post()` locked-assessment pattern verbatim (checked in `get()`/`post()` rather than `dispatch()` so `LoginRequiredMixin`'s auth check always runs first) — a code review flagged this duplication as a candidate for a shared mixin, but with only two occurrences and the spec explicitly calling for "the same posture as the Guidance step," extracting an abstraction now was judged premature.

As in the spec, this step is reachable only by direct URL for now — no link exists yet from the Assessment detail (hub) page. That wiring is deferred to the hub page slice (`05-hub-page-and-mark-complete.md`), as intended.
