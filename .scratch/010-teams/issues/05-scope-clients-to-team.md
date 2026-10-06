# 05 — Scope Clients to the Team

**What to build:** Advisors only ever see and act on their own Team's Clients; another Team's Client behaves as if it doesn't exist. Add `Client.objects.for_team(team)` and route every Client lookup through it with a 404 on miss (ADR 0013 — explicit, greppable lookups; a small view mixin/helper is fine if the lookup stays explicit). Covers: Client list, detail and update pages; the Client count on the home page; the Assessment start form's Client dropdown (built with the requesting User's Team); and validation on Assessment start so that posting another Team's Client id is rejected even if submitted directly. See PRD § Scoping; user stories 16–19, 24, 25, 27, 28.

**Blocked by:** 03 — Client Team ownership and Created By.

**Status:** ready-for-agent

- [ ] `Client.objects.for_team(team)` returns only that Team's Clients.
- [ ] The Client list shows only the requesting User's Team's Clients.
- [ ] Client detail and update return 404 for another Team's Client and work normally for the owning Team.
- [ ] The home page Client count reflects only the requesting User's Team.
- [ ] The Assessment start form's Client dropdown lists only the requesting User's Team's Clients.
- [ ] Posting the Assessment start form with another Team's Client id does not create an Assessment (form error or 404).
- [ ] Tests (Django test client) set up data for two Teams and cover each of the above, including the other-Team 404s.
- [ ] Full test suite passes.
