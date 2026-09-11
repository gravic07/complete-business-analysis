# 02 — Staff-side Generate/Copy/Revoke/Regenerate controls

**What to build:** The advisor-facing half of the feature — the ability to generate, copy, revoke, and regenerate a Client Access Link for either step, from every location the spec calls for.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers.

**Status:** done

- [x] Advisor sees Generate controls for both the Guidance step and the Answer Questions step on the assessment-detail hub's in-progress boxes, whenever the Assessment isn't complete.
- [x] The same controls also appear on the dedicated Guidance and Answer Questions pages themselves.
- [x] Generate is replaced with a direct link to the Client's edit page when that Client has no email on file, rather than a dead-end disabled button.
- [x] Once generated, the link's URL is displayed as copyable text plus a "Copy" button, alongside "Revoke" and "Regenerate" actions.
- [x] Revoke immediately disables the link and returns that step's control to the Generate state.
- [x] Regenerate immediately reflects a new URL, invalidating the old one, while remaining in the active/copyable state.
- [x] All new staff-side endpoints require login, consistent with every other view in the `assessments` app.
- [x] Controls for a step disappear once the Assessment is marked complete.

## Comments

Implemented in `assessments/views.py` (`ClientAccessLinkGenerateView`, `ClientAccessLinkRevokeView`, `ClientAccessLinkRegenerateView`, sharing a `ClientAccessLinkActionView` base for login/setup/redirect handling), `assessments/urls.py` (`<pk>/access-link/<link_type>/{generate,revoke,regenerate}/`), and a shared `snippets/assessments/access-link-controls.html` template included from the assessment-detail hub (both boxes) and the dedicated Guidance/Answer pages. Revoke/Regenerate are scoped to an *active* link only, so a stale page can't reactivate an already-revoked link and bypass Generate's email check.

While building the "no email → edit Client" fallback, found that `ClientForm` never actually exposed an `email` field (ticket 01 added it to the model but not the form/template) — that would have been a real dead end, so fixed it here as part of closing out this ticket: `clients/forms.py` and `templates/form_fields/client-fields.html`, with new tests in `clients/tests.py`.

The Client-facing link URL (`/client-access/<token>/`) is built from a hardcoded path constant (`CLIENT_ACCESS_LINK_PATH_TEMPLATE` in `views.py`) rather than `reverse()`, since the `client_portal` app (tickets 03-05) doesn't exist yet — it's the one place to update once that app's URLconf lands.

Ran `/code-review` (8 parallel angles) and addressed the confirmed findings: the `ClientForm` gap above, the hardcoded URL centralized into a named constant, duplicate link-lookup code consolidated into `_get_active_link()`, an N+1 query on the detail hub fixed (single `ClientAccessLink` query split by `link_type` instead of two), and a clipboard-API guard added in `project.js`. 24 new backend tests plus 2 client-form tests; full suite (301 tests) passing; ruff/mypy/djlint clean on everything touched. Marked `done` — awaiting review/merge.
