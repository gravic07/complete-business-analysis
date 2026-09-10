Status: ready-for-agent

# Client Access Links for Category Guidance and Answer Questions

## Problem Statement

Advisors often aren't in the same room as the Client when the Guidance step ("Concerns, Priorities and Goals") or the Answer Questions step of an Assessment needs to be filled in. Today both steps are only reachable through login-required pages meant for the advisor, so if the advisor and Client are working remotely, the advisor has no way to let the Client contribute directly — everything has to be relayed through the advisor by phone, email, or a separate meeting.

## Solution

Add Client Access Links: a per-Assessment, per-step (Guidance or Answer Questions), advisor-generated URL that a Client can open without logging in. The advisor generates the link on demand, copies it out of the app, and sends it to the Client through whatever channel they'd normally use (this feature does not send the email itself). Opening the link requires the Client to enter the email address on file for that Client as a lightweight verification step. Once verified, the Client sees a minimal, instructional standalone page and the same underlying Guidance or Answer form an advisor would use — on the Guidance page, relabeled "Concerns, Priorities and Goals" for the Client's benefit. Data saved through either page goes through the exact same save path as an advisor's own submission, with no way to tell afterward who entered it. Submitting never marks the Assessment complete — that stays an exclusively advisor-driven action. Links remain valid until the Assessment is marked complete, and the advisor can Revoke or Regenerate a link at any time.

## User Stories

1. As an advisor, I want to add an email address to a Client, so that I have somewhere to send that Client's access links.
2. As an advisor, I want the email field on Client to be optional, so that adding it doesn't force me to go back and edit every existing Client record before I can use any other part of the app.
3. As an advisor, I want a "Generate" action for the Guidance step on an in-progress Assessment's detail page, so that I can create a Client Access Link the moment I decide to send it.
4. As an advisor, I want the same Generate action available for the Answer Questions step, so that I can send either step independently depending on what the Client needs to do.
5. As an advisor, I want the Generate action for a given step to be replaced with a direct link to edit the Client when that Client has no email on file, so that I'm guided straight to the fix instead of hitting a dead end.
6. As an advisor, I want the generated link displayed as copyable text plus a "Copy" button, so that I can paste it into whatever channel I use to reach the Client.
7. As an advisor, I want the same Generate/Copy/Revoke/Regenerate controls to also appear on the dedicated Guidance and Answer Questions pages (not only the assessment-detail hub), so that I can send a link while I'm already working on that step.
8. As an advisor, I want a Revoke action on an active Client Access Link, so that I can immediately cut off access if it was sent to the wrong person or I need to stop further edits.
9. As an advisor, I want a Regenerate action on an active Client Access Link, so that I can issue a fresh URL that invalidates the old one, without a separate revoke-then-generate step.
10. As an advisor, I want Generate to be available again after a link has been revoked, so that I can issue a brand-new link for that step whenever I need to.
11. As an advisor, I want a Client Access Link to keep working even after that step shows "Done," so that the Client can revisit and revise their answers or guidance up until I finalize the Assessment.
12. As an advisor, I want both Client Access Links for an Assessment to stop working the instant I mark the Assessment complete, so that a Client can never edit data behind an already-finalized Assessment, regardless of the link's own stored status.
13. As an advisor, I want the Client Access Link controls visible only while the Assessment isn't yet complete, so that irrelevant controls don't linger once the Assessment is done.
14. As an advisor, I want data a Client enters through their link saved through the exact same Guidance/Answer save path I use myself, so that there's no special-cased data or extra step needed on my end to make use of it.
15. As an advisor, I want a Client's submission through either link to never mark the Assessment complete, so that Mark Complete stays a deliberate action only I can take.
16. As an advisor, I want the existing "Done"/"Not done" indicators to update the same way regardless of whether the Client or I entered the data, so that I always have an accurate view of the Assessment's progress.
17. As a Client without a login, I want to open the link my advisor sent me and see clear instructions about what I'm being asked to do, so that I understand the purpose of the page before I start.
18. As a Client, I want to be asked for my email address before I can see or fill in the actual form, so that a stray or guessed link can't expose my advisor's data about my business to someone else.
19. As a Client, I want a generic, non-revealing message if I enter an email that doesn't match, so that the page doesn't confirm any details about the Assessment to someone who isn't me.
20. As a Client, I want the page to look like a simple, standalone form with no unrelated navigation or internal tool chrome, so that I'm not confused by controls that aren't meant for me.
21. As a Client, I want the Category Guidance step presented to me as "Concerns, Priorities and Goals," so that the language matches how I'd actually describe what I'm entering, rather than internal advisor terminology.
22. As a Client, I want every field on the Concerns, Priorities and Goals page to remain optional, so that I'm not forced to write something for a category I have nothing to add for.
23. As a Client, I want the Answer Questions page to work exactly like it would for my advisor, so that I answer the same questions the same way regardless of who fills them in.
24. As a Client, I want a clear confirmation after I save, telling me my responses were saved and that I can return using the same link to make changes later, so that I know the submission worked and I'm not locked out afterward.
25. As a Client, I want to be warned before I navigate away from the page with unsaved changes, so that I don't accidentally lose my input by closing the tab or hitting back.
26. As a Client, I want to see a clear, friendly message if my link has been deactivated, so that I know to contact my advisor rather than assuming the page is broken.
27. As a developer, I want a single `ClientAccessLink` model governing both step types (`link_type` of `guidance` or `answer`), so that Generate/Revoke/Regenerate logic isn't duplicated across two separate models.
28. As a developer, I want the link's token to be a fully opaque, cryptographically random string used directly as the URL path segment, so that no combination of guessing or enumeration can derive a valid link from an Assessment's UUID.
29. As a developer, I want link validity — status plus the parent Assessment's completion state — checked on every request to a Client-facing view, so that Revoke and Mark Complete both take effect immediately rather than only at the Client's next fresh page load.
30. As a developer, I want email verification checked live against the current `Client.email` on every page load, with no session or cookie persisting a "verified" state, so that a staff correction to the email takes effect immediately and no trust is silently carried between visits.
31. As a developer, I want the Client-facing views to reuse the existing `CategoryGuidanceForm`/`AssessmentAnswerForm` classes unchanged, so that Client-submitted data is identical in shape and validation to advisor-submitted data with no parallel logic to maintain.
32. As a developer, I want no field anywhere recording whether a given `CategoryGuidance` or `Answer` was entered by the advisor or by a Client via a link, so that downstream consumers (AI prompts, reports) never need to special-case the two paths.

## Implementation Decisions

### Schema Changes

**`Client.email`** — new `EmailField(blank=True, default="")` on the existing `Client` model (`clients` app). Optional, format-validated by Django's `EmailField`, no uniqueness constraint.

**`ClientAccessLink`** — new model in the `assessments` app (mirrors `CategoryGuidance`'s placement alongside `Assessment`). Fields: `assessment` FK (cascade delete), `link_type` (`CharField` with choices `guidance` / `answer`), `token` (`CharField`, unique, indexed, generated via `secrets.token_urlsafe(32)` — ~43 opaque characters, bearing no derivable relationship to the Assessment's UUID), `status` (`CharField` with choices `active` / `revoked`, default `active`). `unique_together = [["assessment", "link_type"]]` — exactly one row per (Assessment, step). Uses the project's standard `BaseModel` (UUID pk, `created_at`/`updated_at`) for its internal identity; `token`, not the pk, is the externally-facing lookup key.

### Modules

**Link lifecycle helpers** — small functions, no HTTP concerns, callable from both the staff-side views and (for validity checks) the Client-facing views:
- *Generate*: creates a `ClientAccessLink` row with a fresh token and `status="active"` for a given (Assessment, link_type). Only invoked when no row exists yet, or the existing row is `revoked`.
- *Revoke*: sets `status="revoked"` on the existing row. No replacement token is issued.
- *Regenerate*: overwrites the existing row's `token` with a fresh value in place, leaves `status="active"`. No history of the prior token is kept.
- *Is valid*: given a token, resolves the `ClientAccessLink` (or nothing, for an unrecognized token) and reports valid only when `status="active"` **and** the parent `Assessment.status != "complete"` — the Assessment's own completion state overrides a link's stored `active` status, so completing an Assessment implicitly invalidates both its links without needing to touch the `ClientAccessLink` rows themselves.

**Staff-side controls** — new POST endpoints scoped under the Assessment's pk and a `link_type` path segment (Generate, Revoke, Regenerate), reachable from both the assessment-detail hub's in-progress boxes and the existing `CategoryGuidanceView`/`AssessmentAnswerView` staff pages. All require `LoginRequiredMixin`, matching every other staff-facing view in the `assessments` app. Each box/page renders one of two states per step: no active link (or a revoked one) → "Generate" (itself replaced by a link to the Client's edit page when `Client.email` is blank) → an active link → the token URL as copyable text plus a "Copy" button, "Revoke", and "Regenerate".

**New `client_portal` app** — houses the Client-facing, unauthenticated surface, kept separate from the staff-authenticated `assessments`/`clients`/`reports` apps so "no login required" is a property of an entire app rather than an exception carved out of an authenticated one. Contains:
- A single URL entry point per token, e.g. `client-access/<str:token>/`, dispatching internally on the resolved `ClientAccessLink.link_type` to render either the Answer flow or the "Concerns, Priorities and Goals" flow.
- A view that, on a fresh `GET`, always renders an email-only gate (no session or cookie is consulted). On `POST` with the email, the view checks the link's validity (per the helper above) and compares the submitted email case-insensitively against the live `assessment.client.email`; on a match, it renders the underlying `CategoryGuidanceForm`/`AssessmentAnswerForm` in the same response, carrying the token and verified email forward as hidden fields so the form's own save `POST` can be re-validated (link validity + email match) without asking the Client to retype their email for that same in-progress fill. Reloading the URL fresh (refresh, reopening the tab, returning later) always starts back at the email gate.
- An invalid/unrecognized token, a revoked link, or a link whose Assessment is now complete each render a distinct, friendly terminal page (not a bare 404) — the revoked/completed case explicitly tells the Client to contact their advisor; an unrecognized token renders a generic "this link isn't valid" page with no further detail.
- A minimal standalone base template (header showing the Client's contact name and business name, no staff-app navigation/sidebar) that the gate, the two form flows, and the confirmation/terminal pages all extend.
- On successful save, a confirmation view/state telling the Client their response was saved and that they can return via the same link to make further changes.
- A small inline script implementing a `beforeunload`-style guard on the form pages, active whenever the form has unsaved edits, warning the Client before they navigate away.

**Rebranding** — the "Concerns, Priorities and Goals" label is applied purely in `client_portal`'s templates around the unmodified `CategoryGuidanceForm`. No new field, model, or conditional logic is added to `CategoryGuidance` or its staff-facing form/template to support the rebrand.

**Instructional copy** — static text authored directly in the `client_portal` templates for each step's gate and form page. Not sourced from any database-backed or admin-editable field; future wording changes are a normal code change and deploy.

### Routing

- New `assessments` app URLs, scoped under the Assessment's pk: Generate/Revoke/Regenerate POST endpoints per `link_type`.
- New top-level `client_portal` app URLs: the single `client-access/<str:token>/` entry point (GET for the gate/form, POST for both the email check and the underlying form save).
- No changes to any existing `assessments`, `clients`, or `reports` URL.

## Testing Decisions

Good tests here verify observable behavior at the view/HTTP boundary and persisted model state — response status codes, redirects, rendered page content, and the rows left behind in the database — not internal helper call counts or query plans. Prior art: `reports/tests/test_pdf_template_view.py` and `reports/tests/test_trigger_pdf_export_view.py` establish the pattern of Django `TestCase`/pytest-django tests driving views through `django.test.Client` and `reverse()`, including the codebase's one existing precedent for an unauthenticated, token-gated view.

- **Link lifecycle helpers** — direct tests against Generate/Revoke/Regenerate/Is-valid, using `Assessment`/`ClientAccessLink` fixtures. Cases: Generate creates an active row when none exists; Generate creates a new row when the existing one is revoked; Revoke flips status with no new token; Regenerate changes the token while leaving status active; Is-valid returns invalid for a revoked link, invalid for an otherwise-active link whose Assessment is complete, and valid otherwise.
- **Staff-side endpoints** — authenticated `django.test.Client` hitting the Generate/Revoke/Regenerate endpoints. Assert Generate is rejected (or unreachable) when `Client.email` is blank; assert each action's effect on the persisted `ClientAccessLink` row; assert the assessment-detail and guidance/answer pages render the correct control state (Generate vs. Copy/Revoke/Regenerate) based on the link's current status and the Assessment's completion state.
- **Client-facing flow** — unauthenticated `django.test.Client` hitting `client-access/<token>/`. Cases: unrecognized token → generic invalid-link page; revoked link → friendly deactivated-link message; link on a completed Assessment → same terminal treatment even though the row's own `status` may still read `active`; wrong email → generic access-denied message with no Assessment detail leaked in the response; correct email → the underlying form renders, and submitting it creates/updates the same `CategoryGuidance`/`Answer` rows an advisor's submission would, without ever setting `Assessment.status="complete"` (it may still advance `draft → in_progress`, matching today's advisor-path behavior); a fresh `GET` after a successful email check does not skip the gate (no session persistence).
- **Rebrand** — assert the Client-facing Guidance page renders "Concerns, Priorities and Goals" copy while the existing staff-facing Guidance page still renders "Category Guidance," from the same underlying form/model.

## Out of Scope

- Actually sending the link to the Client by email or any other channel — the advisor copies and sends it manually.
- Rate limiting or lockout after repeated wrong-email attempts.
- Any audit/history trail of prior tokens after a Regenerate.
- Any session-based or "remember me" trust for the Client across separate page loads.
- An admin-editable field for the instructional copy — it's static template text per ADR-0012.
- Any UI for reopening/undoing Mark Complete, or for reviving a Client Access Link once its Assessment is complete.
- Multiple contact emails per Client, or sending one link to more than one recipient.
- Any way to distinguish, after the fact, whether the advisor or the Client entered a given piece of Guidance or Answer data.
- Any change to Assessment completion rules or the existing completion-readiness checker from ADR-0011 — unchanged by this feature.

## Further Notes

- This spec implements the decision recorded in ADR-0012 (persisted opaque token over signed URLs or session-based trust); ADR-0011 (Assessment's draft/in_progress/complete lifecycle) remains the governing model for completion and is unchanged.
- `CONTEXT.md` has already been updated with the `ClientAccessLink` and "Concerns, Priorities and Goals" glossary entries and the new `Client.email` field — no further glossary work should be needed unless implementation surfaces new vocabulary.
- Unrelated pre-existing observation, out of scope here: `ClientListView`/`ClientDetailView` currently have no `LoginRequiredMixin` at all. Not to be "fixed" as a side effect of this work — flagging only so it isn't mistaken for something this feature introduced.
