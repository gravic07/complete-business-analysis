# 03 — Client Team ownership and Created By

**What to build:** Every Client is owned by a Team, and every Client, Assessment, Feedback and PDFExport records who created it. Nothing is filtered by Team yet (tickets 05–07), but after this ticket every record has an owner, all existing data belongs to "Peak Performance Partners", and every existing User is in that Team. See PRD § Schema changes, § Migrations, § Scoping (creation stamping), § Admin, § Management command; `CONTEXT.md` → Team, Created By; ADR 0013.

Schema: `Client.team` (FK to Team, NOT NULL, PROTECT) and `created_by` (FK to User, NOT NULL, PROTECT) on Client, Assessment, Feedback and PDFExport. No `team` on any other model.

Migrations, in three steps:
1. Add `Client.team` and the four `created_by` fields as nullable.
2. Data migration: if any User or any Client/Assessment/Feedback/PDFExport row exists, create Team "Peak Performance Partners", put every existing User in it (superusers included), set every Client's `team` to it, and set `created_by` on every existing Client/Assessment/Feedback/PDFExport to the earliest-created superuser (falling back to the earliest-created User). Raise with a clear message if such rows exist but no User does. Do nothing on an empty database. Reverse: null out the populated fields; don't delete the Team.
3. Make `Client.team` and the four `created_by` fields NOT NULL.

Creation stamping — every path that creates these records sets `created_by = request.user` (and, for Clients, `team = request.user.team`): Client create (UI), Client create (API), Assessment start, Feedback submit, PDF export trigger. The Client form never exposes `team`. `generate_test_assessment` gains `--user` (email), defaulting to the earliest-created superuser and erroring clearly if none exists.

Admin: Client gets a Team list column, list filter and editable Team field, plus a `created_by` column; Assessment, Feedback and PDFExport get a `created_by` column.

Factories: `ClientFactory` sets `created_by` and derives `team` from that User's Team; `AssessmentFactory` sets `created_by`; add Feedback/PDFExport factories if tests need them.

**Blocked by:** 02 — Team model and membership.

**Status:** ready-for-agent

- [ ] `Client.team` and the four `created_by` fields exist and are NOT NULL after migrating; all use PROTECT.
- [ ] Migrating an empty database creates no Team and succeeds.
- [ ] Migrating a database with existing Users and data creates "Peak Performance Partners", assigns every User and every Client to it, and stamps `created_by` per the rule above (verified manually against a copy of production data — no automated migration test, per PRD).
- [ ] The data migration raises a clear error when Team-owned rows exist but no User does.
- [ ] Creating a Client through the UI or API stamps the creator's Team and the creator as `created_by`; the Client form has no Team field.
- [ ] Starting an Assessment, submitting Feedback and triggering a PDF export each stamp the requesting User as `created_by`.
- [ ] `generate_test_assessment --user <email>` stamps that User; with no `--user` it stamps the earliest superuser; with no superuser it errors clearly. Covered via `call_command`.
- [ ] Admin shows the Team column/filter/field on Client and the `created_by` column on all four models.
- [ ] Deleting a User who created any of these records is refused.
- [ ] Tests (Django test client) cover the stamping on each creation path.
- [ ] Full test suite passes.
