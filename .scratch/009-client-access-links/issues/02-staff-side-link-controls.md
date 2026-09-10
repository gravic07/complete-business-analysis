# 02 — Staff-side Generate/Copy/Revoke/Regenerate controls

**What to build:** The advisor-facing half of the feature — the ability to generate, copy, revoke, and regenerate a Client Access Link for either step, from every location the spec calls for.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers.

**Status:** ready-for-agent

- [ ] Advisor sees Generate controls for both the Guidance step and the Answer Questions step on the assessment-detail hub's in-progress boxes, whenever the Assessment isn't complete.
- [ ] The same controls also appear on the dedicated Guidance and Answer Questions pages themselves.
- [ ] Generate is replaced with a direct link to the Client's edit page when that Client has no email on file, rather than a dead-end disabled button.
- [ ] Once generated, the link's URL is displayed as copyable text plus a "Copy" button, alongside "Revoke" and "Regenerate" actions.
- [ ] Revoke immediately disables the link and returns that step's control to the Generate state.
- [ ] Regenerate immediately reflects a new URL, invalidating the old one, while remaining in the active/copyable state.
- [ ] All new staff-side endpoints require login, consistent with every other view in the `assessments` app.
- [ ] Controls for a step disappear once the Assessment is marked complete.
