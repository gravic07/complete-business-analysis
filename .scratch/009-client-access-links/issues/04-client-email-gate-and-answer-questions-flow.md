# 04 — Client email gate + Answer Questions flow

**What to build:** The first full end-to-end Client-facing path: opening an Answer-type link, passing the email gate, and saving Answers through the existing form logic — plus the shared unsaved-changes guard the Guidance flow (ticket 05) will reuse.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers; 03 — Client portal scaffold + terminal states.

**Status:** done

- [x] A fresh `GET` on a valid, active Answer-type link always renders the email-only gate — no session or cookie is consulted, and a refresh or reopened tab always returns to the gate.
- [x] Submitting a non-matching email returns a generic denial message that reveals no Assessment detail.
- [x] Submitting the Client's current (live) `Client.email` renders the Answer Questions form through the unmodified `AssessmentAnswerForm`, carrying the token and verified email forward as hidden fields so the save step doesn't re-prompt for email within the same visit.
- [x] Saving the form persists `Answer` rows identically to the advisor-facing flow (same snapshot behavior, same per-question validation), and never sets `Assessment.status` to `complete` — though it may still advance `draft` to `in_progress` exactly as the advisor path does today.
- [x] After saving, the Client sees a confirmation message stating their response was saved and that they can return via the same link to make further changes.
- [x] The shared base template includes a `beforeunload`-style guard, active whenever the form has unsaved edits, that warns before navigating away.

## Comments

Replaced ticket 03's placeholder response in `ClientAccessLinkEntryView` (`client_portal/views.py`) with the full Answer-type flow. Resolution and the terminal-state/link-type checks now happen once in an overridden `dispatch()` (instead of being duplicated across `get()`/`post()`), which stores the resolved link on `self.link` for the rest of the request.

- **Email gate** — `ClientEmailGateForm` (new `client_portal/forms.py`), rendered by `GET`/on a failed check. No session or cookie is ever consulted; every fresh `GET` renders the gate from scratch.
- **Email check POST** — compares the submitted address case-insensitively against the live `assessment.client.email` (re-queried each request, never cached/snapshotted). A mismatch adds a generic non-field error to the same gate form (`EMAIL_DENIAL_MESSAGE`) — no assessment or client detail is included in that response.
- **Answer form POST** — detected by the presence of a `verified_email` field in `request.POST` (vs. a plain `email` field for the gate check). Re-validates both the hidden `token` and `verified_email` against the live link/email before binding the unmodified `AssessmentAnswerForm`; a stale/tampered pair sends the client back to a fresh gate rather than trusting the client-carried values. `assessments/forms.py` and `assessments/models.py` are untouched — the save path (snapshotting, per-question validation, draft→in_progress advance, never setting `complete`) is exactly the advisor-facing one.
- **Confirmation page** — `answer-saved.html`, shown after a successful save, states the response was saved and that the Client can return via the same link to make changes.
- **Unsaved-changes guard** — a small inline script in the shared `client_portal/base.html`'s `inline_javascript` block: tracks `input`/`change` on the page's form, clears on `submit`, and calls `preventDefault()`/sets `event.returnValue` in `beforeunload` only while dirty. Lives in the shared base template (not per-page) so ticket 05's Guidance flow picks it up for free.

Two things surfaced and fixed via `/code-review` (Standards + Spec axes):
- **Standards** — the `get()`/`post()` duplication above (fixed by moving resolution into `dispatch()`), and the category/field-rendering markup duplicated between the new `answer-questions.html` and the existing advisor-facing `assessment-answer.html` (extracted into a shared `snippets/assessments/answer-form-fields.html`, included from both).
- **Spec** — ticket 03's still-active "shared header shows the linked Client's business name and contact name" requirement wasn't being honored on any of this ticket's new pages; the pre-verification gate/denial pages correctly keep generic branding (nothing to show safely yet), but the post-verification Answer form and confirmation page now pass `client` into context so the header renders as intended once the email check has passed.

11 new tests in `client_portal/tests.py` (17 total in that file); full suite (318 tests) passing; ruff/mypy clean on everything touched (the same two pre-existing, unrelated mypy errors in `assessments/forms.py` remain, untouched by this ticket). Ticket 05 (Concerns, Priorities and Goals flow) is next and reuses this ticket's gate/dispatch shape and the shared guard.
