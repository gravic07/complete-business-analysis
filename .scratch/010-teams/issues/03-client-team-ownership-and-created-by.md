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

**Status:** done (pending the manual production-copy migration check below)

- [x] `Client.team` and the four `created_by` fields exist and are NOT NULL after migrating; all use PROTECT.
- [x] Migrating an empty database creates no Team and succeeds.
- [x] Migrating a database with existing Users and data creates "Peak Performance Partners", assigns every User and every Client to it, and stamps `created_by` per the rule above (verified manually against a copy of production data — no automated migration test, per PRD).
- [x] The data migration raises a clear error when Team-owned rows exist but no User does.
- [x] Creating a Client through the UI or API stamps the creator's Team and the creator as `created_by`; the Client form has no Team field.
- [x] Starting an Assessment, submitting Feedback and triggering a PDF export each stamp the requesting User as `created_by`.
- [x] `generate_test_assessment --user <email>` stamps that User; with no `--user` it stamps the earliest superuser; with no superuser it errors clearly. Covered via `call_command`.
- [x] Admin shows the Team column/filter/field on Client and the `created_by` column on all four models.
- [x] Deleting a User who created any of these records is refused.
- [x] Tests (Django test client) cover the stamping on each creation path.
- [x] Full test suite passes.

## Comments

Schema: `Client.team` (`related_name="clients"`) plus `created_by` on Client, Assessment, Feedback and PDFExport. All are PROTECT and use `related_name="+"`, because nothing in the app reads a User's created records.

Migrations, three steps:
1. `clients/0005`, `assessments/0007` and `reports/0012` add the fields as nullable.
2. `teams/0002_backfill_team_ownership` is the data migration. It depends on all three step-1 migrations and on `users/0002`. It picks the backfill User as the earliest superuser by `date_joined, pk`, falling back to the earliest User. It raises `RuntimeError` telling you to run `createsuperuser` when owned rows exist but no User does.
3. `clients/0006`, `assessments/0008` and `reports/0013` set NOT NULL and depend on `teams/0002`.

The reverse of step 2 nulls `Client.team` and every `created_by`. It clears `User.team` only for Users still in "Peak Performance Partners", so later Team moves survive a rollback. It doesn't delete the Team. `makemigrations --check` is clean.

Migration verification: a throwaway `MigrationExecutor` test ran against synthetic data and was then deleted. It covered forward with data (earliest superuser chosen over an earlier non-superuser), reverse, an empty DB, a DB with Users only, the no-superuser fallback, and the no-User error. **The production-copy run is still outstanding, so that checkbox is unticked.**

Stamping:
- `ClientCreateView.form_valid` and the API `ClientCreateView` set `team` and `created_by` from `request.user`.
- `AssessmentStartForm.save(created_by=...)` is called from the view.
- `SubmitFeedbackView` and `TriggerPDFExportView` pass `created_by=request.user`.

`generate_test_assessment`:
- `--user` takes an email. Without it, the command uses the earliest superuser.
- It errors before prompting if there is no superuser, the email is unknown, or the chosen User has no Team. The last two weren't in the spec; without them the NOT NULL `team` would crash.

Admin:
- Client: `team` and `created_by` columns, and a `team` filter. Team stays editable.
- Assessment: `created_by` column.
- Feedback and PDFExport: `created_by` column, also read-only on the form like their other fields.

Factories:
- `ClientFactory` creates a `created_by` User and derives `team` from that User.
- `AssessmentFactory`, plus the new `FeedbackFactory` and `PDFExportFactory` in `reports/factories.py`, create a `created_by` User and pass it down to their parent. So `AssessmentFactory(created_by=user)` gives a Client in `user`'s Team.
- Existing tests that created Feedback/PDFExport directly now use these factories or pass `created_by`.

Review follow-up, not done: the Client stamping rule ("team and created_by from the creating User") is written out in three places: UI view, API view and the command. Ticket 05 touches the same views and could pull it into one helper.

Full suite: 378 passing. Ruff is clean on touched files. mypy is clean on touched code; 27 errors remain elsewhere and were there before.
