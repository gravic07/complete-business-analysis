# 04 — No-team gate

**What to build:** A logged-in User with no Team can't use the app and is told why. Add a middleware, placed after `LoginRequiredMiddleware`, that redirects any authenticated User whose `team` is empty to a new no-team page — except for: the no-team page itself, allauth account pages (logout, password change, MFA, etc.), Django admin, the client portal, the PDF template page, and static/media. For `/api/` requests it returns a 403 JSON response with an explanatory message instead of redirecting. The no-team page (login-required) shows "Your account isn't assigned to a team yet. Ask an administrator to add you.", the User's email, and a logout button. The navbar hides the Clients and Assessments links and the Team name for a User with no Team, showing only My Profile and logout (no Admin link). See PRD § No-team gate; `CONTEXT.md` → Team.

**Blocked by:** 01 — Site-wide login required; 02 — Team model and membership.

**Status:** ready-for-agent

- [ ] A logged-in User with no Team who requests any app page (e.g. Client list, home) is redirected to the no-team page.
- [ ] The no-team page renders the explanatory copy, the User's email and a logout button; an anonymous request to it redirects to login.
- [ ] A User with no Team can still reach logout and their allauth account pages, and a staff User with no Team can still use Django admin.
- [ ] Client portal pages and the PDF template signed-token path are unaffected for anyone.
- [ ] A `/api/` request from a User with no Team returns 403 with a JSON message.
- [ ] A User with a Team is never redirected; a User newly assigned to a Team reaches the app on their next request without logging out.
- [ ] The navbar hides the Clients/Assessments links and the Team name for a User with no Team, and shows them for a Team member.
- [ ] Tests (Django test client) cover each of the above.
- [ ] Full test suite passes.
