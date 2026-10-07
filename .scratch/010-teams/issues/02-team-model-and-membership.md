# 02 — Team model and membership

**What to build:** Platform admins can create Teams and put Users in them, and an advisor sees which Team they're in. Add a new `teams` app with a `Team` model (project `BaseModel`, `name` only) registered in Django admin. Add a nullable `User.team` FK (`on_delete=PROTECT`, so a Team with members can't be deleted). The User admin gets a Team field on the form plus a Team list column and list filter. The navbar shows the logged-in User's Team name when they have one. Test factories gain a `TeamFactory`, and `UserFactory` assigns a Team by default so existing logged-in tests keep working. See PRD § New `teams` app, § Schema changes, § Admin; `CONTEXT.md` → Team.

This ticket adds no ownership to Clients and no data migration — existing Users are left with no Team until ticket 03's backfill.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `Team` model exists with a `name`, and is creatable/editable in Django admin.
- [x] `User.team` is a nullable FK to Team; deleting a Team that still has members is refused.
- [x] User admin shows Team on the edit form, as a list column, and as a list filter; a platform admin can assign, change and clear a User's Team.
- [x] The navbar shows the Team name for a logged-in User who has a Team, and shows nothing Team-related for a User without one.
- [x] `TeamFactory` exists; `UserFactory` produces a User with a Team by default, with an easy way to produce one without.
- [x] Tests cover the navbar Team name (shown for a Team member) and PROTECT on Team deletion.
- [x] Full test suite passes.

## Comments

New `teams` app (`teams/{apps,models,admin,factories,tests}.py`, migration `teams/0001_initial`), registered in `LOCAL_APPS` after `core`. `Team(BaseModel)` has only `name`; its `Meta` inherits `BaseModel.Meta` but orders by `name`. `TeamAdmin` mirrors `ClientAdmin` (list/search on name, read-only id/timestamps).

`User.team` (migration `users/0002_user_team`): `ForeignKey("teams.Team", on_delete=PROTECT, null=True, blank=True, related_name="members")`. `blank=True` is what lets admin clear a User's Team. `related_name="members"` was not in the spec, but it gives later tickets `team.members`.

User admin: a new "Team" fieldset on the change form, `team` in `list_display`, `team` prepended to the inherited auth `list_filter`, and `list_select_related = ["team"]` so the column adds no per-row queries.

Navbar (`templates/snippets/navigation.html`): `{{ request.user.team.name }}` appears in a `navbar-item` span, before the Profile dropdown, only when the User has a Team. The span has `data-testid="navbar-team"` so the no-Team test has something to assert is absent. This costs one Team query per authenticated page. That's acceptable for now; ticket 04's no-Team gate may want a `current_team` context processor that removes it.

Factories: `TeamFactory` lives at `teams/factories.py`, following the `clients/factories.py` convention. `UserFactory` gains `team = SubFactory(TeamFactory)`; `UserFactory.create(team=None)` gives a User with no Team. pytest-django's `admin_client`/`admin_user` don't go through the factory, so admin users in tests have no Team, which matches platform admins.

Tests: `teams/tests.py` covers the navbar with and without a Team, PROTECT on deleting a Team that has members, creating a Team in admin, and the factory default. `users/tests/test_admin.py` covers the changelist Team filter and assign/move/clear through the change form. Full suite: 353 passing. Ruff and mypy are clean on the touched code, and `makemigrations --check` is clean. The `/code-review` run found no spec gaps; the only change applied was rewriting the assign/move/clear test parametrisation as explicit booleans.
