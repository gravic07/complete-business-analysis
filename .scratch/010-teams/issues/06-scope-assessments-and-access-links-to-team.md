# 06 — Scope Assessments and ClientAccessLinks to the Team

**What to build:** Advisors can only view and change their own Team's Assessments and ClientAccessLinks. Add `for_team(team)` on Assessment (via its Client's Team) and ClientAccessLink (via its Assessment's Client's Team), and route every lookup through them with a 404 on miss (ADR 0013). Covers: Assessment detail, Answer Questions, Guidance, Mark Complete, ClientAccessLink Generate/Revoke/Regenerate, and the Assessment count on the home page. Client portal access via a ClientAccessLink token stays Team-agnostic and unchanged. See PRD § Scoping; user stories 20, 21, 27, 38.

**Blocked by:** 03 — Client Team ownership and Created By.

**Status:** ready-for-agent

- [ ] `Assessment.objects.for_team(team)` and `ClientAccessLink.objects.for_team(team)` return only records whose Client belongs to that Team.
- [ ] Assessment detail, Answer Questions, Guidance and Mark Complete return 404 (GET and POST) for another Team's Assessment and work normally for the owning Team.
- [ ] Generate, Revoke and Regenerate a ClientAccessLink return 404 for another Team's Assessment and change nothing.
- [ ] The home page Assessment count reflects only the requesting User's Team.
- [ ] Moving a Client to another Team in admin makes its Assessments visible to the new Team and invisible to the old one.
- [ ] Client portal pages reached through a valid token behave exactly as before.
- [ ] Tests (Django test client) set up data for two Teams and cover each of the above.
- [ ] Full test suite passes.
