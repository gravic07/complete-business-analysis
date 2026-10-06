# 02 — Team model and membership

**What to build:** Platform admins can create Teams and put Users in them, and an advisor sees which Team they're in. Add a new `teams` app with a `Team` model (project `BaseModel`, `name` only) registered in Django admin. Add a nullable `User.team` FK (`on_delete=PROTECT`, so a Team with members can't be deleted). The User admin gets a Team field on the form plus a Team list column and list filter. The navbar shows the logged-in User's Team name when they have one. Test factories gain a `TeamFactory`, and `UserFactory` assigns a Team by default so existing logged-in tests keep working. See PRD § New `teams` app, § Schema changes, § Admin; `CONTEXT.md` → Team.

This ticket adds no ownership to Clients and no data migration — existing Users are left with no Team until ticket 03's backfill.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `Team` model exists with a `name`, and is creatable/editable in Django admin.
- [ ] `User.team` is a nullable FK to Team; deleting a Team that still has members is refused.
- [ ] User admin shows Team on the edit form, as a list column, and as a list filter; a platform admin can assign, change and clear a User's Team.
- [ ] The navbar shows the Team name for a logged-in User who has a Team, and shows nothing Team-related for a User without one.
- [ ] `TeamFactory` exists; `UserFactory` produces a User with a Team by default, with an easy way to produce one without.
- [ ] Tests cover the navbar Team name (shown for a Team member) and PROTECT on Team deletion.
- [ ] Full test suite passes.
