Status: ready-for-agent

# Hub page and Mark Complete action

## What to build

Make the existing Assessment detail page state-aware, tying the Guidance step, Answer step, and a new Mark Complete action together into one coherent flow, and wire Mark Complete into today's report-generation trigger.

**`AssessmentDetailView` (hub) — draft/in_progress state**: shows a link to the Guidance step and a link to the Answer step, each indicating whether it's been done (guidance: `guidance_submitted_at` is set; answers: every template question has an `Answer`). Shows a Mark Complete button, calling the completion readiness checker from issue 01 to decide whether it's enabled; when disabled, shows why (which step is unfinished). Both steps are reachable in any order — no gating between them.

**`AssessmentDetailView` (hub) — complete state**: unchanged existing read-only summary (grouped answers, analyses list), plus each category's `CategoryGuidance` text displayed alongside its answers. Categories with no guidance entered show nothing extra for that section — no empty placeholder.

**Mark Complete endpoint** — a POST view scoped to the Assessment pk. Calls the completion readiness checker; if ineligible, rejects the request (400 or redirect back with an error message) — this must be enforced server-side, not just via the disabled button, since a stale page or direct POST could otherwise bypass it. If eligible: sets `status="complete"`, then redirects to `reports:report?autostart=1` for that assessment — the same redirect `AssessmentEntryView.form_valid` produces today, so the existing autostart JS and `TriggerAnalysisView`/`start_analysis` machinery on the report page picks it up unchanged. No changes needed to those.

**Routing** — new URL for the Mark Complete POST endpoint, scoped under the Assessment pk. Hub page template links to the Guidance URL (issue 03) and Answer URL (issue 04) and posts to this new endpoint.

## Acceptance criteria

- [ ] Hub page for a `draft`/`in_progress` Assessment shows links to Guidance and Answer steps with accurate "done"/"not done" indicators
- [ ] Mark Complete button is disabled (with a reason shown) when the readiness checker says ineligible
- [ ] Mark Complete button is enabled when the readiness checker says eligible
- [ ] POSTing Mark Complete while ineligible is rejected server-side: no status change, no Analysis created
- [ ] POSTing Mark Complete while eligible sets `status="complete"` and redirects to the report page with `autostart=1`
- [ ] After Mark Complete, the report page's existing autostart flow triggers the first Analysis exactly as it does today for a freshly-submitted assessment (no changes to `TriggerAnalysisView`/`start_analysis`)
- [ ] Hub page for a `complete` Assessment renders the existing grouped-answers/analyses summary unchanged
- [ ] Hub page for a `complete` Assessment additionally shows each category's guidance text where present, and shows nothing extra for categories with no guidance
- [ ] Guidance and Answer step links/pages are reachable in any order — neither is gated on the other
- [ ] Tests cover: readiness-gated button state, server-side rejection when ineligible, successful completion + redirect, and complete-state guidance display

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs the readiness checker
- `03-category-guidance-step.md` — needs the Guidance step to link to and to check completion of
- `04-answer-step-refactor.md` — needs the Answer step to link to and to check completion of
