# 01 — Site-wide login required

**What to build:** Every page in the app requires login by default, so no view can be left exposed by a forgotten mixin. Enable Django's `LoginRequiredMiddleware` and explicitly opt out the pages that must stay public: allauth account pages (login, signup, password reset, email confirmation, etc.), the client portal (ClientAccessLink entry and its Guidance/Answer pages), and the PDF template page (which keeps its existing logic — signed-token access for the PDF renderer, otherwise logged-in). `/api/` routes are excluded from the middleware and keep relying on DRF's authentication (`IsAuthenticated` is already the default), so token-authenticated API calls keep working. This closes the existing gap where the Client list/create/detail/edit pages are reachable without logging in. See PRD § Site-wide login.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `LoginRequiredMiddleware` is enabled site-wide.
- [ ] An anonymous request to the Client list, create, detail and edit pages redirects to login.
- [ ] Login, signup, password reset and email-confirmation pages remain reachable anonymously.
- [ ] ClientAccessLink pages (entry, email gate, Guidance, Answer Questions, terminal states) remain reachable anonymously and behave exactly as before.
- [ ] The PDF template page still renders for a valid signed token without login, and still renders for a logged-in User; an anonymous request without a valid token is still refused.
- [ ] A token-authenticated API request still succeeds; an unauthenticated API request still gets DRF's 401/403, not an HTML redirect.
- [ ] Existing per-view `LoginRequiredMixin`s may stay or go, but behavior is unchanged for logged-in Users.
- [ ] Tests (Django test client) cover anonymous redirect on the Client pages and continued anonymous access to allauth, client portal and PDF signed-token paths.
- [ ] Full test suite passes.
