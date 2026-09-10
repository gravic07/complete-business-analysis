# 05 — Concerns, Priorities and Goals (Guidance) flow

**What to build:** The second Client-facing path, reusing ticket 04's gate/dispatch machinery, wired to the Guidance step and rebranded for the Client as "Concerns, Priorities and Goals."

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers; 03 — Client portal scaffold + terminal states; 04 — Client email gate + Answer Questions flow.

**Status:** ready-for-agent

- [ ] Guidance-type links go through the same gate mechanics as the Answer flow: fresh-load re-verification (no session), live email check, generic denial message on mismatch.
- [ ] Verified access renders the existing `CategoryGuidanceForm` unchanged, with all Client-facing labels and copy relabeled as "Concerns, Priorities and Goals" — every category field remains optional.
- [ ] Saving persists `CategoryGuidance` rows identically to the advisor-facing flow, with no new fields, model changes, or conditional logic added to `CategoryGuidance` itself.
- [ ] The existing staff-facing Guidance page and admin continue to show "Category Guidance" unchanged.
- [ ] After saving, the Client sees the same confirmation/return-via-link messaging as the Answer flow.
- [ ] The unsaved-changes guard from ticket 04 applies here via the shared base template, with no duplicated implementation.
