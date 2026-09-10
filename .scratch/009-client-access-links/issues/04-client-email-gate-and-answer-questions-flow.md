# 04 — Client email gate + Answer Questions flow

**What to build:** The first full end-to-end Client-facing path: opening an Answer-type link, passing the email gate, and saving Answers through the existing form logic — plus the shared unsaved-changes guard the Guidance flow (ticket 05) will reuse.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers; 03 — Client portal scaffold + terminal states.

**Status:** ready-for-agent

- [ ] A fresh `GET` on a valid, active Answer-type link always renders the email-only gate — no session or cookie is consulted, and a refresh or reopened tab always returns to the gate.
- [ ] Submitting a non-matching email returns a generic denial message that reveals no Assessment detail.
- [ ] Submitting the Client's current (live) `Client.email` renders the Answer Questions form through the unmodified `AssessmentAnswerForm`, carrying the token and verified email forward as hidden fields so the save step doesn't re-prompt for email within the same visit.
- [ ] Saving the form persists `Answer` rows identically to the advisor-facing flow (same snapshot behavior, same per-question validation), and never sets `Assessment.status` to `complete` — though it may still advance `draft` to `in_progress` exactly as the advisor path does today.
- [ ] After saving, the Client sees a confirmation message stating their response was saved and that they can return via the same link to make further changes.
- [ ] The shared base template includes a `beforeunload`-style guard, active whenever the form has unsaved edits, that warns before navigating away.
