# 05 — Concerns, Priorities and Goals (Guidance) flow

**What to build:** The second Client-facing path, reusing ticket 04's gate/dispatch machinery, wired to the Guidance step and rebranded for the Client as "Concerns, Priorities and Goals."

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers; 03 — Client portal scaffold + terminal states; 04 — Client email gate + Answer Questions flow.

**Status:** done

- [x] Guidance-type links go through the same gate mechanics as the Answer flow: fresh-load re-verification (no session), live email check, generic denial message on mismatch.
- [x] Verified access renders the existing `CategoryGuidanceForm` unchanged, with all Client-facing labels and copy relabeled as "Concerns, Priorities and Goals" — every category field remains optional.
- [x] Saving persists `CategoryGuidance` rows identically to the advisor-facing flow, with no new fields, model changes, or conditional logic added to `CategoryGuidance` itself.
- [x] The existing staff-facing Guidance page and admin continue to show "Category Guidance" unchanged.
- [x] After saving, the Client sees the same confirmation/return-via-link messaging as the Answer flow.
- [x] The unsaved-changes guard from ticket 04 applies here via the shared base template, with no duplicated implementation.

## Comments

Replaced ticket 04's placeholder branch in `ClientAccessLinkEntryView.dispatch()` (`client_portal/views.py`) — the `link_type != ANSWER` early return — with real Guidance-type handling. `dispatch()` now only resolves terminal states and stores `self.link`; `get()`/`post()`/`_render_gate()`/`_handle_email_check()` branch internally on `self.link.link_type` to reach either the existing Answer path or the new Guidance one, so the gate mechanics (fresh-load re-verification, live email check, generic denial message) are shared code, not a parallel implementation.

- **Category scoping** — the Guidance flow needs the same "categories in play for this Assessment's template" query the staff `CategoryGuidanceView` already computed inline. Extracted it to `assessments/services.py::categories_for_template()` and pointed both call sites at it, rather than duplicating the queryset a third time.
- **Save path** — `CategoryGuidanceForm` doesn't own its persistence (unlike `AssessmentAnswerForm.save()`); the update_or_create/delete-per-category + `guidance_submitted_at` stamp + draft→in_progress advance previously lived only in `CategoryGuidanceView.form_valid()`. Extracted that into `assessments/services.py::save_category_guidance()`, called from both the staff view and the new `client_portal` handler, so there's one save path, not two copies of the same logic.
- **Templates** — new `guidance-gate.html`, `concerns-priorities-goals.html`, `guidance-saved.html` under `templates/pages/client_portal/`, all extending the shared `base.html` (so the unsaved-changes guard applies with zero new code) and carrying the "Concerns, Priorities and Goals" rebrand. Extracted the category-field-loop markup (previously inline in `assessment-guidance.html`) into `snippets/assessments/guidance-form-fields.html`, shared between the staff and Client-facing templates — mirrors ticket 04's `answer-form-fields.html` snippet for the Answer flow.
- **Staff page untouched** — `assessment-guidance.html`'s copy, `CategoryGuidanceForm`, `CategoryGuidance`, and the admin inline are unchanged; the rebrand is purely in the new `client_portal` templates.

11 new tests in `client_portal/tests.py` (28 total in that file, mirroring ticket 04's Answer-flow coverage plus a blank-guidance-deletes-existing-row case and a rebrand-copy assertion); full suite (329 tests) passing; ruff clean; mypy clean on everything touched (the same two pre-existing, unrelated mypy errors in `assessments/forms.py` remain). Two findings from `/code-review` were fixed before commit: the category queryset was duplicated instead of shared (extracted to `categories_for_template()`), and `_render_guidance_form` was re-querying categories even when a bound form (which already carries its own `.categories`) was passed in.
