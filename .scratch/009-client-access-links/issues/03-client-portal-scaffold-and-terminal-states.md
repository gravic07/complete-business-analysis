# 03 — Client portal scaffold + terminal states

**What to build:** The public, unauthenticated surface a Client's link resolves into — the new `client_portal` app, its single token-keyed entry point, the shared minimal layout, and the non-functional terminal pages a Client can land on before any email gate or form logic exists.

**Blocked by:** 01 — Client email field + ClientAccessLink schema & lifecycle helpers.

**Status:** ready-for-agent

- [ ] A new `client_portal` app exposes a single URL entry point keyed on a `ClientAccessLink` token.
- [ ] Visiting an unrecognized token renders a generic "this link isn't valid" page, with no further detail.
- [ ] Visiting a revoked link renders a distinct, friendly "this link is no longer active — contact your advisor" page.
- [ ] Visiting a link whose parent Assessment is now complete renders the same friendly deactivated-link treatment, even though the row's own `status` may still read `active`.
- [ ] All portal pages extend a shared, minimal standalone base template — header showing the linked Client's contact name and business name, no staff-app navigation or sidebar.
- [ ] No view in `client_portal` requires login.
