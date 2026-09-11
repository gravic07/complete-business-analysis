# 03 — Client portal scaffold + terminal states

**What to build:** The public, unauthenticated surface a Client's link resolves into — the new `client_portal` app, its single token-keyed entry point, the shared minimal layout, and the non-functional terminal pages a Client can land on before any email gate or form logic exists.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers.

**Status:** done

- [x] A new `client_portal` app exposes a single URL entry point keyed on a `ClientAccessLink` token.
- [x] Visiting an unrecognized token renders a generic "this link isn't valid" page, with no further detail.
- [x] Visiting a revoked link renders a distinct, friendly "this link is no longer active — contact your advisor" page.
- [x] Visiting a link whose parent Assessment is now complete renders the same friendly deactivated-link treatment, even though the row's own `status` may still read `active`.
- [x] All portal pages extend a shared, minimal standalone base template — header showing the linked Client's contact name and business name, no staff-app navigation or sidebar.
- [x] No view in `client_portal` requires login.

## Comments

Implemented as a new top-level `client_portal` app (`complete_business_analysis_tool/client_portal/`), registered in `LOCAL_APPS` and mounted at `client-access/` in `config/urls.py`. `ClientAccessLinkEntryView` (`client_portal/views.py`) resolves the token once and renders one of the two terminal templates under `templates/pages/client_portal/` (`invalid-link.html` for an unrecognized token — 404 — or `deactivated-link.html` for a revoked link or one whose Assessment is complete — 200), both extending a shared `base.html` that overrides `base.html`'s `navigation` block with a minimal header showing the linked Client's business name and contact name (falling back to generic branding when no Client is known, i.e. the unrecognized-token case). A still-valid link currently gets a plain placeholder response — the email gate and per-step form flows are tickets 04-05, which this scaffold unblocks.

While wiring the entry point's URL name, also closed the TODO ticket 02 left behind: `assessments/views.py`'s `_access_link_state` now builds `access_link_url` via `reverse("client_portal:entry", ...)` instead of the hardcoded `CLIENT_ACCESS_LINK_PATH_TEMPLATE` constant (removed), so the staff-facing link and the client_portal route can no longer drift out of sync.

Extracted `client_access_link_grants_access(link)` in `assessments/services.py` — the revoked/assessment-complete predicate factored out of `is_client_access_link_valid(token)` — so the new entry view can reuse it against the row it already fetched instead of re-querying by token, and so `_access_link_state` (staff detail hub / step pages) shares the same predicate instead of re-implementing "assessment not complete" inline (`link.assessment` reuses the caller's already-loaded `Assessment` via a manual FK-cache assignment, avoiding an N+1). Found via `/code-review`.

6 new tests in `client_portal/tests.py`; full suite (307 tests) passing; ruff/mypy/djlint clean on everything touched (two pre-existing, unrelated mypy errors in `assessments/forms.py` left as-is). Marked `done` — awaiting review/merge; ticket 04 (email gate + Answer Questions flow) is next.
