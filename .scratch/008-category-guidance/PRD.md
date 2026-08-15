Status: ready-for-agent

# Category Guidance Before Assessment Questions

## Problem Statement

Advisors often already know, before they start an Assessment, which topics within a Category deserve extra AI attention — a nuance the standard multiple-choice Questions don't capture. Today there is no way to supply that insight until *after* a Report has been generated: the advisor must complete the entire Assessment, wait for the first Analysis, and only then submit Feedback to steer a re-analysis. That means the first-pass Report is always written blind to context the advisor already had, and getting it right requires a wasted feedback cycle.

## Solution

Add a Category Guidance step to the Assessment flow: optional free-text notes, one per Category, that an advisor can enter to steer AI generation before any Question is answered. Guidance and Questions become independent steps reachable in any order once the Assessment exists, and the Assessment itself gains an explicit lifecycle (`draft → in_progress → complete`) instead of being created only at the very end. The advisor explicitly marks an Assessment complete once both steps are done — that action, not "last question answered," is what triggers the first Analysis. Guidance persists and is passed into every subsequent Analysis run for that Assessment, labeled separately from Feedback so the model doesn't conflate "focus on this" with "revise this."

## User Stories

1. As an advisor, I want to select a Client and AssessmentTemplate and immediately have an Assessment created in draft state, so that I have a persistent record to attach Guidance and Answers to from the very start.
2. As an advisor, I want a dedicated Guidance step listing every Category in the Assessment's template, so that I can enter free-text notes per Category before answering any Questions.
3. As an advisor, I want every field on the Guidance step to be optional, so that I'm not forced to write something for Categories where I have nothing to add.
4. As an advisor, I want the Guidance step itself to be mandatory to submit — even if I leave every field blank — so that Mark Complete has an unambiguous signal that I've had the chance to provide guidance.
5. As an advisor, I want to reach the Guidance step and the Questions step in either order, so that I can answer questions first and add guidance afterward if that fits how I work with a given Client.
6. As an advisor, I want to revise Guidance I already entered at any point before the Assessment is marked complete, so that I can refine my notes as I learn more while working through the Questions.
7. As an advisor, I want a single hub page for an in-progress Assessment that links to the Guidance step and the Questions step, so that I always know what's left to do.
8. As an advisor, I want the hub page to show a Mark Complete action, so that I have an explicit, deliberate way to finalize the Assessment.
9. As an advisor, I want Mark Complete to be unavailable until I've submitted the Guidance step and answered every Question, so that I can't accidentally finalize an Assessment that's missing required input.
10. As an advisor, I want Mark Complete to trigger the first Analysis automatically, so that the flow matches today's behavior of generating a Report immediately after finishing an Assessment.
11. As an advisor, I want my Guidance to be preserved and passed into every future re-analysis for that Assessment (not just the first one), so that my upfront context keeps steering the Report even after I submit Feedback cycles later.
12. As an advisor, I want the AI to receive my Guidance and my later Feedback as distinctly labeled inputs, so that a forward-looking focus area I named early isn't confused with a correction I made after reading generated content.
13. As an advisor, I want to see the Guidance I entered for each Category displayed on the Assessment detail page once the Assessment is complete, so that I can recall what I asked the AI to emphasize when I'm interpreting the resulting Report.
14. As an advisor, I want Categories with no Guidance entered to simply show nothing (not an empty placeholder record), so that the detail page and admin views stay uncluttered.
15. As an advisor, I want existing, already-completed Assessments to be unaffected by this change — they should show as complete with no disruption to their Reports or Feedback history.
16. As an advisor, I want the Guidance step to only list Categories that are actually part of the selected AssessmentTemplate, so that I'm not asked about Categories irrelevant to this Assessment.
17. As a developer, I want a single function that determines whether an Assessment is eligible for Mark Complete, so that the same rule governs both the UI (enabling the button) and server-side validation (rejecting an invalid request), with no risk of the two drifting apart.
18. As an advisor, I want the Mark Complete action to be rejected server-side (not just hidden in the UI) if the requirements aren't actually met, so that a stale page or direct request can't finalize an incomplete Assessment.

## Implementation Decisions

### Schema Changes

**`Assessment.status`** — CharField with choices `draft`, `in_progress`, `complete`. Set to `draft` on creation. Set to `in_progress` automatically the first time either the Guidance step or the Answer step is submitted (whichever happens first). Set to `complete` only by the Mark Complete action — never inferred from finishing a step.

**`Assessment.guidance_submitted_at`** — nullable `DateTimeField`. Set when the advisor submits the Guidance step (regardless of how many fields were filled in). This is the authoritative signal that the Guidance step is done — it must not be inferred from the presence/absence of `CategoryGuidance` rows, since a submission with every field left blank produces zero rows.

**`CategoryGuidance` model** — new model in the `assessments` app (mirrors `CategoryFeedback`'s shape). Fields: `assessment` FK (cascade delete), `category` FK, `text` TextField. A row is created only for Categories where the advisor entered non-blank text; Categories left blank get no row.

**Migration/backfill** — existing Assessments (all fully answered under the old flow) are backfilled to `status="complete"` and `guidance_submitted_at=created_at`. No `CategoryGuidance` rows are created for them — they simply have no guidance text, which is accurate to their history and avoids them appearing to be missing a step that didn't exist when they were created.

### Modules

**Completion readiness checker** — a function taking an `Assessment` and returning whether it is eligible for Mark Complete, plus which condition (if any) is unmet: `guidance_submitted_at is not None` and every Question in the Assessment's template has a corresponding `Answer`. No side effects, no HTTP concerns — callable from both the hub page (to enable/disable the Mark Complete button) and the Mark Complete endpoint (to reject the request server-side if the gate isn't met). This is the one piece of genuinely reusable, independently testable logic in this feature.

**`AssessmentStartForm` / `AssessmentStartView`** — replaces the client-selection portion of today's `AssessmentEntryForm`/`AssessmentEntryView`. Takes a Client and AssessmentTemplate (template still comes from the URL, as today), creates the `Assessment` in `draft` status, and redirects to the hub page (the existing Assessment detail URL). This is the new entry point linked from the template list page and the client detail page's "Start an assessment…" control, replacing their current links to the old entry view.

**`CategoryGuidanceForm` / `CategoryGuidanceView`** — dynamically builds one optional text field per Category present in the Assessment's template (Categories reachable via `Category.objects.filter(questions__template_questions__template=assessment.template).distinct()`, since no Answers exist yet to derive Categories from). On submit: creates `CategoryGuidance` rows for non-blank fields only, stamps `guidance_submitted_at`, and advances `status` to `in_progress` if still `draft`. Pre-fills existing `CategoryGuidance` text so revisiting the step shows what was already entered. Available for editing any time before `status` reaches `complete`.

**`AssessmentAnswerForm` / `AssessmentAnswerView`** — the existing dynamic question-building logic from `AssessmentEntryForm`, minus the `client` field and minus Assessment creation. Operates against an existing (draft/in_progress) Assessment: creates one `Answer` per Question, same snapshot behavior as today, same single-submit-all-at-once UX (incremental per-answer autosave is out of scope — see below). Advances `status` to `in_progress` if still `draft`. Requires all Questions to be answered in one submission, matching today's validation.

**Mark Complete endpoint** — a thin POST view. Calls the completion readiness checker; if not eligible, rejects with an error (defense in depth — the button is also disabled client-side when not eligible). If eligible, sets `status="complete"` and redirects to `reports:report?autostart=1` for that Assessment — identical to today's post-submit redirect from `AssessmentEntryView.form_valid`. No changes needed to `TriggerAnalysisView`, `start_analysis`, or the autostart JS on the report page; this endpoint just originates the same redirect from a different trigger point.

**Assessment detail page (hub)** — `AssessmentDetailView` and its template become state-aware:
- `draft` / `in_progress`: shows links to the Guidance step and the Answer step (each indicating whether it's been done), and the Mark Complete button (disabled with an explanation when the readiness checker says it isn't eligible yet).
- `complete`: shows today's existing read-only summary (grouped answers, analyses list), plus each Category's Guidance text displayed alongside its answers. Categories with no Guidance entered show nothing for that section.

**AI prompt integration** — `reports/ai_service.py::_build_category_prompt()` gains a `guidance_text` parameter, appended as its own labeled line (e.g. "Advisor guidance provided before the assessment: …"), separate from the existing `feedback_text` line ("Advisor feedback to incorporate: …"). `analysis/tasks.py` fetches the Assessment's `CategoryGuidance` per Category (via `assessment.category_guidance.all()` or equivalent) and passes it through to `generate_category_section()` on every Analysis run — the initial run and every later re-analysis — independent of what `combined_feedback` resolves to for that run.

### Routing

- Template list page and client detail page's "Start an assessment…" link now point at `AssessmentStartView` instead of the old `AssessmentEntryView`.
- The existing Assessment detail URL (`assessments:detail`) becomes the hub for all statuses — no new URL for the hub itself.
- New URLs: the Guidance step, the Answer step, and the Mark Complete POST endpoint, each scoped under the Assessment's pk.
- `AssessmentEntryView`/`AssessmentEntryForm` are removed once the three replacement views are in place — no dual-path support needed since this repo has no external consumers of the old entry URL besides its own templates.

## Testing Decisions

Good tests verify observable behavior at a stable interface boundary — form/view outcomes and persisted state, not internal helper calls or query counts.

**Completion readiness checker** — Unit tests, no DB mocking needed beyond building `Assessment`/`Answer`/`CategoryGuidance` fixtures. Cases: neither step done → ineligible with both reasons; guidance done, answers incomplete → ineligible; answers done, guidance not submitted → ineligible; both done → eligible. Highest-value target — pure logic shared by two call sites, so a bug here silently affects both the button and the server-side gate identically.

**Status transitions (`draft → in_progress → complete`)** — Django `TestCase`, mirroring how `Analysis` status transitions are tested today. Assert a fresh Assessment starts `draft`; assert submitting either the Guidance form or the Answer form (in either order) advances it to `in_progress`; assert Mark Complete advances it to `complete` only when the readiness checker allows it, and is rejected (with no status change) when it doesn't.

**`CategoryGuidance` save behavior** — Django `TestCase` against `CategoryGuidanceForm`. Assert blank fields produce no `CategoryGuidance` row; non-blank fields persist correctly; `guidance_submitted_at` is stamped on submit regardless of how many fields were filled; resubmitting with revised text updates existing rows rather than duplicating them.

**AI prompt integration** — Test at the `_build_category_prompt()` / `generate_category_section()` boundary, following existing prompt-building test patterns in the `reports`/`analysis` apps. Assert `guidance_text` appears as its own labeled line distinct from `feedback_text` when both are present; assert guidance is included in a second (re-)analysis run, not only the first.

**Mark Complete endpoint** — Django `TestCase` with a test client. POST when ineligible → assert rejection, no status change, no Analysis created. POST when eligible → assert `status="complete"`, an Analysis is created (mock/assert `start_analysis` is invoked or its side effect), and the response redirects to the report page with `autostart=1`.

## Out of Scope

- Incremental per-answer autosave for the Questions step (flagged in ADR-0011 as an immediate follow-up, not bundled here). The Answer step remains a single all-at-once submission.
- Any change to how `Feedback`/`CategoryFeedback` work post-Report — that flow is untouched.
- Per-user ownership/permissions on Assessments (still just `LoginRequiredMixin`, no change).
- Any UI for reopening a `complete` Assessment back to `in_progress`.
- Any additional intake steps beyond Guidance and Questions (future work referenced in ADR-0011, not designed here).
- Bulk/administrative editing of Guidance outside the advisor-facing flow.

## Further Notes

- ADR-0011 documents the decision to give `Assessment` an explicit draft/in_progress/complete lifecycle instead of a session-backed multi-step form, specifically because planned future intake steps need to work across different machines and different users — a persisted status survives that handoff, session state doesn't.
- `CONTEXT.md` has been updated with the `Assessment Status` and `CategoryGuidance` glossary terms, and a new Prompt Design Rule documenting the distinct-labeling requirement for Guidance vs. Feedback.
- `CategoryGuidance` is intentionally modeled as its own table rather than reusing `CategoryFeedback` — the two have different lifecycles (editable-until-complete vs. append-only per Feedback cycle) and different scope (every Analysis run vs. triggering one specific re-analysis), and conflating them would make the "which categories were reprocessed by this re-analysis" logic in `analysis/tasks.py` harder to reason about.
