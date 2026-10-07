# 04 — No-team gate

**What to build:** A logged-in User with no Team can't use the app and is told why. Add a middleware, placed after `LoginRequiredMiddleware`, that redirects any authenticated User whose `team` is empty to a new no-team page — except for: the no-team page itself, allauth account pages (logout, password change, MFA, etc.), Django admin, the client portal, the PDF template page, and static/media. For `/api/` requests it returns a 403 JSON response with an explanatory message instead of redirecting. The no-team page (login-required) shows "Your account isn't assigned to a team yet. Ask an administrator to add you.", the User's email, and a logout button. The navbar hides the Clients and Assessments links and the Team name for a User with no Team, showing only My Profile and logout (no Admin link). See PRD § No-team gate; `CONTEXT.md` → Team.

**Blocked by:** 01 — Site-wide login required; 02 — Team model and membership.

**Status:** done

- [x] A logged-in User with no Team who requests any app page (e.g. Client list, home) is redirected to the no-team page.
- [x] The no-team page renders the explanatory copy, the User's email and a logout button; an anonymous request to it redirects to login.
- [x] A User with no Team can still reach logout and their allauth account pages, and a staff User with no Team can still use Django admin.
- [x] Client portal pages and the PDF template signed-token path are unaffected for anyone.
- [x] A `/api/` request from a User with no Team returns 403 with a JSON message.
- [x] A User with a Team is never redirected; a User newly assigned to a Team reaches the app on their next request without logging out.
- [x] The navbar hides the Clients/Assessments links and the Team name for a User with no Team, and shows them for a Team member.
- [x] Tests (Django test client) cover each of the above.
- [x] Full test suite passes.

## Comments

`core/middleware.py` defines `NoTeamGateMiddleware`, which runs right after `SiteLoginRequiredMiddleware`. It checks `user.team_id` on every request, so assigning a Team takes effect immediately.

Exemptions, checked in `_is_exempt`:
- Views marked with the new `team_not_required` decorator: `NoTeamView` and the User's profile views (`users:detail`, `users:update`, `users:redirect`). The profile views were added at the user's request, so that My Profile in the navbar works for a User without a Team.
- Any view that can be reached anonymously (`login_not_required`). This covers the client portal, `PDFTemplateView` and the media `serve` view without extra wiring. This is intentional and confirmed: if a page doesn't require authentication, it doesn't require a Team either. Every page requires login unless it specifically opts out.
- Django admin, matched with `resolver_match.app_name == "admin"`.
- allauth views, matched by module prefix (`allauth.`). This depends on allauth's package layout.
- Static files never reach the gate, because WhiteNoise serves them before the middleware runs.

`/api/` requests:
- The middleware skips these. A new DRF permission, `HasTeam` in `api/permissions.py`, guards them instead. It is set in `DEFAULT_PERMISSION_CLASSES` alongside `IsAuthenticated`.
- A User with no Team gets a 403 JSON response (`{"detail": ...}`). This holds for any login method, because DRF has already authenticated the request (session or token) by the time permissions run.
- Anonymous requests pass `HasTeam`, so they still get DRF's normal authentication failure.
- `api/views/clients.py` set its own `permission_classes = [IsAuthenticated]`, which would have dropped the default `HasTeam`. That override was removed.
- Guard test: `api/tests.py::test_every_api_view_requires_a_team` walks every `/api/` route and fails if a view lacks `HasTeam`.
  - Exempt by design (`TEAM_EXEMPT_API_ROUTES`): `obtain_auth_token` (no auth at all), and `api-schema` / `api-docs` (admin-only via `SPECTACULAR_SETTINGS.SERVE_PERMISSIONS`).
  - Any new API view that overrides `permission_classes` must include `HasTeam`, or be added to that set deliberately.

Profile:
- `UserDetailView` is now limited to the requesting User: `get_queryset` filters to `request.user`, so any other pk returns 404. This was added at the user's request.

No-team page:
- `NoTeamView` lives at `/no-team/` (`name="no_team"`) and renders `pages/no-team.html`.

Navbar:
- The Clients and Assessments links are hidden unless `request.user.team` is set.
- The pre-existing "Report an issue" dropdown item is still shown to Users without a Team.

Tests:
- `conftest.py` overrides pytest-django's `admin_user` fixture so the admin belongs to a Team. Without this, the API docs and schema tests would hit the gate.
- There is no static/media test. Media is exempt through `login_not_required` (verified by reading the code).
