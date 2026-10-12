# 05 — Scope Clients to the Team

**What to build:** Advisors only ever see and act on their own Team's Clients; another Team's Client behaves as if it doesn't exist. Add `Client.objects.for_team(team)` and route every Client lookup through it with a 404 on miss (ADR 0013 — explicit, greppable lookups; a small view mixin/helper is fine if the lookup stays explicit). Covers: Client list, detail and update pages; the Client count on the home page; the Assessment start form's Client dropdown (built with the requesting User's Team); and validation on Assessment start so that posting another Team's Client id is rejected even if submitted directly. See PRD § Scoping; user stories 16–19, 24, 25, 27, 28.

**Blocked by:** 03 — Client Team ownership and Created By.

**Status:** done

- [x] `Client.objects.for_team(team)` returns only that Team's Clients.
- [x] The Client list shows only the requesting User's Team's Clients.
- [x] Client detail and update return 404 for another Team's Client and work normally for the owning Team.
- [x] The home page Client count reflects only the requesting User's Team.
- [x] The Assessment start form's Client dropdown lists only the requesting User's Team's Clients.
- [x] Posting the Assessment start form with another Team's Client id does not create an Assessment (form error or 404).
- [x] Tests (Django test client) set up data for two Teams and cover each of the above, including the other-Team 404s.
- [x] Full test suite passes.

## Comments

`clients/models.py` adds `ClientQuerySet.for_team(team)`, exposed as `Client.objects`. It accepts `Team | None`, because `User.team` is nullable. `None` matches nothing, since every Client has a Team.

Views:
- `ClientListView`, `ClientDetailView` and `ClientUpdateView` each define their own `get_queryset` that calls `Client.objects.for_team(self.request.user.team)`. Because `get_object` uses that queryset, another Team's Client returns 404.
- I chose per-view lookups over a mixin. They are explicit and greppable, as ADR 0013 asks, and a mixin was awkward to type under mypy.
- `ClientListView` no longer uses `ordering` and calls `.order_by("business_name")` itself. The ordering is unchanged.
- The `HomeView` Client count is scoped. The Assessment and Analysis counts on the home page are left to issues 06 and 07.

Assessment start:
- `AssessmentStartForm` now takes a required `team` kwarg, which `AssessmentStartView` passes from the request.
- The Client dropdown is built from `Client.objects.for_team(team)`. Posting another Team's Client id fails with the standard "Select a valid choice" error, not a 404. The spec allows either.
- The `?client=` prefill is still unscoped. An id from another Team leaves the dropdown unselected and can't be submitted.

Tests:
- Existing Client view and start view tests now create their Client with `created_by=user`, so the Client is in the logged-in User's Team.

Review notes (not done):
- User story 28 (the Client detail page lists only that Client's Assessments) holds because the page reads `self.object.assessments`, but no test covers it.
- ADR 0013 says another Team's record returns 404. The start form returns a form error instead, which fits the spirit of the ADR. You could add a line to the ADR if you want that written down.
