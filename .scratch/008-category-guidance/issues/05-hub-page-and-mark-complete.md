Status: complete

# Hub page and Mark Complete action

## What to build

Make the existing Assessment detail page state-aware, tying the Guidance step, Answer step, and a new Mark Complete action together into one coherent flow, and wire Mark Complete into today's report-generation trigger.

**`AssessmentDetailView` (hub) — draft/in_progress state**: shows a link to the Guidance step and a link to the Answer step, each indicating whether it's been done (guidance: `guidance_submitted_at` is set; answers: every template question has an `Answer`). Shows a Mark Complete button, calling the completion readiness checker from issue 01 to decide whether it's enabled; when disabled, shows why (which step is unfinished). Both steps are reachable in any order — no gating between them.

**`AssessmentDetailView` (hub) — complete state**: unchanged existing read-only summary (grouped answers, analyses list), plus each category's `CategoryGuidance` text displayed alongside its answers. Categories with no guidance entered show nothing extra for that section — no empty placeholder.

**Mark Complete endpoint** — a POST view scoped to the Assessment pk. Calls the completion readiness checker; if ineligible, rejects the request (400 or redirect back with an error message) — this must be enforced server-side, not just via the disabled button, since a stale page or direct POST could otherwise bypass it. If eligible: sets `status="complete"`, then redirects to `reports:report?autostart=1` for that assessment — the same redirect `AssessmentEntryView.form_valid` produces today, so the existing autostart JS and `TriggerAnalysisView`/`start_analysis` machinery on the report page picks it up unchanged. No changes needed to those.

**Routing** — new URL for the Mark Complete POST endpoint, scoped under the Assessment pk. Hub page template links to the Guidance URL (issue 03) and Answer URL (issue 04) and posts to this new endpoint.

## Acceptance criteria

- [x] Hub page for a `draft`/`in_progress` Assessment shows links to Guidance and Answer steps with accurate "done"/"not done" indicators
- [x] Mark Complete button is disabled (with a reason shown) when the readiness checker says ineligible
- [x] Mark Complete button is enabled when the readiness checker says eligible
- [x] POSTing Mark Complete while ineligible is rejected server-side: no status change, no Analysis created
- [x] POSTing Mark Complete while eligible sets `status="complete"` and redirects to the report page with `autostart=1`
- [x] After Mark Complete, the report page's existing autostart flow triggers the first Analysis exactly as it does today for a freshly-submitted assessment (no changes to `TriggerAnalysisView`/`start_analysis`)
- [x] Hub page for a `complete` Assessment renders the existing grouped-answers/analyses summary unchanged
- [x] Hub page for a `complete` Assessment additionally shows each category's guidance text where present, and shows nothing extra for categories with no guidance
- [x] Guidance and Answer step links/pages are reachable in any order — neither is gated on the other
- [x] Tests cover: readiness-gated button state, server-side rejection when ineligible, successful completion + redirect, and complete-state guidance display

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs the readiness checker
- `03-category-guidance-step.md` — needs the Guidance step to link to and to check completion of
- `04-answer-step-refactor.md` — needs the Answer step to link to and to check completion of

## Comments

Implemented as specified: `AssessmentDetailView.get_context_data` (`assessments/views.py`) now branches on `assessment.status` — non-complete assessments get a `completion_status` (`assessment_completion_status()`) for the hub's done/not-done indicators and Mark Complete gating; complete assessments keep the existing grouped-answers/analyses summary, now with each category's `CategoryGuidance` text attached (looked up by `category_id`, `None` when no guidance exists for that category). New `MarkCompleteView` (`POST` only, `assessments/<uuid:pk>/complete/`, name `assessments:mark_complete`) re-checks eligibility server-side before flipping `status="complete"` and redirecting to `reports:report?autostart=1` — the same `f"{url}?autostart=1"` redirect the old `AssessmentEntryView.form_valid` used to produce, so `TriggerAnalysisView`/`start_analysis` pick it up unchanged. `assessment-detail.html` is now a single state-aware template: the non-complete branch shows the Guidance/Answer step links with Done/Not done tags and a Mark Complete button/form; the complete branch is the prior template content plus a guidance notification box per category group. Added a `reasons` property to `AssessmentCompletionStatus` (`assessments/services.py`) so both the disabled-button copy and the server-side rejection message explain which condition is unmet. 15 tests added covering every acceptance criterion; full suite (250 tests), ruff, and mypy (no new error categories vs. baseline) all green.

A multi-agent code review during implementation caught three real issues beyond the spec, all fixed before commit:
- `MarkCompleteView` had no guard for a repeat POST against an already-`complete` assessment — since eligibility stays true after completion, a stale double-submit would re-save `status="complete"` and redirect with `autostart=1` again, and since the report page's autostart JS only suppresses itself for a `pending`/`processing` analysis (not `complete`), it would re-trigger a redundant `Analysis` run. Fixed by short-circuiting to a plain (non-autostart) redirect when the assessment is already complete.
- The complete-state answer grouping keyed categories by `Category.name` (which has no uniqueness constraint), so two distinct categories sharing a name would silently merge — one category's answers rendering under the other's heading with its own guidance dropped. Fixed by keying on `category_id` instead, falling back to `None` for answers with no category ("General").
- `completion_status` was computed unconditionally on every detail-page load, including for `complete` assessments where the template never reads it. Moved the computation into the non-complete branch only.

As in the spec, the Guidance and Answer steps remain reachable in either order with no gating between them — the hub only reflects their done/not-done state, it doesn't enforce an order.
