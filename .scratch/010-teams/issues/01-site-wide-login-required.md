# 01 — Site-wide login required

**What to build:** Every page in the app requires login by default, so no view can be left exposed by a forgotten mixin. Enable Django's `LoginRequiredMiddleware` and explicitly opt out the pages that must stay public: allauth account pages (login, signup, password reset, email confirmation, etc.), the client portal (ClientAccessLink entry and its Guidance/Answer pages), and the PDF template page (which keeps its existing logic — signed-token access for the PDF renderer, otherwise logged-in). `/api/` routes are excluded from the middleware and keep relying on DRF's authentication (`IsAuthenticated` is already the default), so token-authenticated API calls keep working. This closes the existing gap where the Client list/create/detail/edit pages are reachable without logging in. See PRD § Site-wide login.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `LoginRequiredMiddleware` is enabled site-wide.
- [x] An anonymous request to the Client list, create, detail and edit pages redirects to login.
- [x] Login, signup, password reset and email-confirmation pages remain reachable anonymously.
- [x] ClientAccessLink pages (entry, email gate, Guidance, Answer Questions, terminal states) remain reachable anonymously and behave exactly as before.
- [x] The PDF template page still renders for a valid signed token without login, and still renders for a logged-in User; an anonymous request without a valid token is still refused.
- [x] A token-authenticated API request still succeeds; an unauthenticated API request still gets DRF's 401/403, not an HTML redirect.
- [x] Existing per-view `LoginRequiredMixin`s may stay or go, but behavior is unchanged for logged-in Users.
- [x] Tests (Django test client) cover anonymous redirect on the Client pages and continued anonymous access to allauth, client portal and PDF signed-token paths.
- [x] Full test suite passes.

## Comments

Added `core/middleware.py::SiteLoginRequiredMiddleware`, a thin subclass of Django 6's `LoginRequiredMiddleware`, registered in `config/settings/base.py` right after `AuthenticationMiddleware`. Its only addition is skipping any request whose `path_info` starts with `/api/`, so every API route (including `api/auth-token/`, `api/schema/`, `api/docs/`) keeps relying solely on DRF authentication + the `IsAuthenticated` default — token requests succeed, unauthenticated ones get DRF's 401/403 instead of an HTML redirect. Chosen over per-view opt-outs because routers/viewsets make decorating every API view brittle.

Opt-outs (`login_not_required`):

- **allauth** — nothing to do; allauth 65.15.1 already decorates its own account/socialaccount/mfa views.
- **Client portal** — `ClientAccessLinkEntryView` (`client_portal/views.py`) via `method_decorator(..., name="dispatch")`. It's the portal's only view, so the entry, email gate, Guidance, Answer Questions and terminal states are all covered.
- **PDF template page** — `PDFTemplateView` (`reports/views.py`), same pattern; its existing `dispatch()` token-or-login logic is unchanged, so an anonymous request without a valid token still gets 403.
- **Dev media** — `config/urls.py` passes `view=login_not_required(serve)` to `static()` so development media serving is unchanged (`static()` is a no-op outside DEBUG).
- **Django admin** — nothing to do; Django decorates `AdminSite.login`. Anonymous `/admin/` now redirects to `/accounts/login/?next=/admin/` rather than `/admin/login/`.

Side effects worth knowing: `/about/` and the DEBUG-only `/400/`–`/500/` preview pages now require login (previously public). Existing `LoginRequiredMixin`s were left in place — redundant but harmless.

New tests in `core/tests.py`: anonymous GET on Client list/create/detail/edit redirects to login with `next`, anonymous POST to create redirects without saving, seven allauth pages reachable anonymously, token-authenticated API request succeeds, unauthenticated API requests get 401/403 with no redirect. Anonymous client-portal and PDF signed-token access are covered by the existing `client_portal/tests.py` and `reports/tests/test_pdf_template_view.py` suites, which now run under the middleware. Full suite (344 tests) passing; ruff clean; mypy clean on touched code (pre-existing unrelated errors in `assessments/forms.py`, `reports/forms.py`, `reports/views.py` unchanged). `/code-review` cleanups applied before commit: type hints on the middleware, a rationale comment on the portal opt-out, and the four Client-page redirect tests merged into one parametrised test.
