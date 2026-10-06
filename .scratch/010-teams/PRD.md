Status: ready-for-agent

# Teams: per-Team data isolation

## Problem Statement

Every logged-in advisor can see and edit every Client, Assessment, Report, Feedback and PDFExport in the system. The app is about to be used by more than one group of advisors, and each group's Clients and their Reports must be invisible to the others. Today there is no notion of ownership at all — no model records which group (or even which User) created it — so there is nothing to filter on.

Two existing gaps make the problem worse:

- The Client list, create, detail and edit pages have no login requirement, so anyone with the URL — logged in or not — can read and edit Client records.
- Generated PDF Reports are served straight from the public media URL with predictable filenames (`{Company}_{AssessmentName}_{YYYYMMDD}.pdf`), bypassing Django entirely, so anyone who can guess a filename can download a Client's Report without logging in.

## Solution

Introduce **Teams** (see `CONTEXT.md` → Team, Created By; ADR 0013). A platform admin creates Teams and assigns Users to them in Django admin. A User belongs to at most one Team; every member of a Team has equal access to all of that Team's data, and data belonging to any other Team behaves as if it doesn't exist (404).

Ownership is stamped on the **Client** — set from the creating User's Team at creation and never editable in the app. Everything downstream of a Client (Assessments, Analysis runs, Reports, Feedback, PDFExports, ClientAccessLinks) belongs to that Client's Team. Client, Assessment, Feedback and PDFExport also record **Created By** as an audit fact, so visibility could be narrowed per-User later without a backfill.

A User with no Team (typically a platform admin) is redirected to a page explaining they must be added to a Team before they can use the app; they can still use Django admin and manage their own account.

The whole site requires login by default, with explicit public exceptions, and PDF Reports are downloaded only through a Team-scoped view.

All existing data belongs to a single Team, "Peak Performance Partners", which the release's data migration creates; every existing User joins it.

## User Stories

1. As a platform admin, I want to create a Team in Django admin, so that I can onboard a new group of advisors.
2. As a platform admin, I want to give a Team a name, so that it's identifiable in admin and in the app.
3. As a platform admin, I want to assign a User to a Team from the User admin page, so that they gain access to that Team's data.
4. As a platform admin, I want to remove a User from their Team (leaving them with no Team), so that I can revoke their app access without deleting their account.
5. As a platform admin, I want to move a User from one Team to another, so that I can reflect a change in who they work with.
6. As a platform admin, I want the Clients a User created to stay with their original Team when that User changes Teams, so that a Team never loses its data because a person moved.
7. As a platform admin, I want to see each Client's Team as a column in the Client admin list, so that I can tell at a glance who owns what.
8. As a platform admin, I want to filter the Client admin list by Team, so that I can review one Team's Clients.
9. As a platform admin, I want to change a Client's Team in Django admin, so that I can correct a mistake or hand a Client over between Teams.
10. As a platform admin, I want every Assessment, Analysis run, Report, Feedback, PDFExport and ClientAccessLink to move automatically when I move a Client to another Team, so that a Client's history is never split across Teams.
11. As a platform admin, I want to see Created By as a column on the Client, Assessment, Feedback and PDFExport admin lists, so that I can audit who created each record.
12. As a platform admin, I want Django admin to refuse to delete a User who has created any Client, Assessment, Feedback or PDFExport, so that the audit trail is never lost — I deactivate them instead.
13. As a platform admin, I want Django admin to refuse to delete a Team that still has members or Clients, so that no data is orphaned or cascaded away by accident.
14. As a platform admin with no Team, I want to still use Django admin, so that I can manage Teams and Users without belonging to any Team myself.
15. As a platform admin, I want to be able to see all Teams' data in Django admin, so that I can support any Team.
16. As an advisor, I want the Client list to show only my Team's Clients, so that I'm not looking at, or able to touch, other Teams' Clients.
17. As an advisor, I want a Client I create to belong to my Team automatically, so that I don't have to choose anything and can't put it in the wrong Team.
18. As an advisor, I want the Client form not to offer a Team field, so that ownership can't be changed from the app.
19. As an advisor, I want to receive "not found" when I open a URL for another Team's Client, so that I learn nothing about whether that record exists.
20. As an advisor, I want "not found" for another Team's Assessment detail, Guidance, Answer Questions and Mark Complete pages, so that I can neither see nor change another Team's Assessments.
21. As an advisor, I want "not found" when trying to Generate, Revoke or Regenerate a ClientAccessLink on another Team's Assessment, so that I can't issue access to another Team's Client.
22. As an advisor, I want "not found" for another Team's Report page, Feedback submission, Assessment Name update and Trigger Analysis action, so that I can't read or alter another Team's Reports.
23. As an advisor, I want "not found" when polling the status of another Team's Analysis run or PDFExport, so that status endpoints can't be used to probe other Teams' data.
24. As an advisor, I want the Assessment start form's Client dropdown to list only my Team's Clients, so that I can't start an Assessment for another Team's Client.
25. As an advisor, I want the Assessment start action to reject another Team's Client even if its id is submitted directly, so that the dropdown isn't the only line of defense.
26. As an advisor, I want all AssessmentTemplates to remain available to me, so that every Team scores against the same shared question bank.
27. As an advisor, I want the home page counts (Clients, Assessments, Analysis runs) to reflect only my Team's data, so that the dashboard is meaningful to me.
28. As an advisor, I want the Client detail page to list only that Client's Assessments, so that nothing from another Team leaks onto it.
29. As an advisor, I want every member of my Team to see and edit everything my Team owns, so that we can cover for each other without permission requests.
30. As an advisor, I want my Team's name shown in the navbar, so that I always know which Team's data I'm working in.
31. As an advisor, I want an Assessment, Feedback or PDFExport I create to record me as its creator, so that there is an audit trail of who did what.
32. As an advisor, I want to download a completed PDF Report through the app, so that I still get the file with its friendly filename.
33. As an advisor, I want PDF Report downloads to require login and membership in the owning Team, so that a guessed or forwarded link never exposes a Client's Report to anyone else.
34. As an advisor, I want "not found" when trying to download another Team's PDF Report, so that the download behaves like every other Team-scoped page.
35. As an advisor using the API to create a Client, I want the Client to be stamped with my Team and me as its creator, so that API-created Clients follow the same rules as UI-created ones.
36. As an anonymous visitor, I want every non-public page to redirect me to login, including the Client pages, so that nothing is exposed by a forgotten login check.
37. As an anonymous visitor, I want the login, signup, password reset and email-verification pages to remain reachable, so that I can actually sign in.
38. As a Client using a ClientAccessLink, I want my link to keep working without logging in, so that remote Guidance and Answer Questions entry is unaffected by Teams.
39. As the PDF renderer, I want the signed-token path of the PDF template page to keep working without a login or Team, so that PDF exports continue to generate in the background.
40. As an advisor viewing the PDF template page directly while logged in, I want it scoped to my Team, so that it can't be used to view another Team's Report.
41. As a logged-in User with no Team, I want to be redirected to a page explaining that my account hasn't been assigned to a Team and that I should ask an administrator, so that I understand why I can't use the app.
42. As a logged-in User with no Team, I want that page to show my email address and a logout button, so that I can confirm which account I'm signed in with and sign out.
43. As a logged-in User with no Team, I want my account pages (logout, password change, MFA) to remain reachable, so that I can still manage my account.
44. As a logged-in User with no Team, I want the navbar to hide the Clients and Assessments links and the Team name, so that I'm not offered links that just bounce me back.
45. As a logged-in User with no Team, I want API requests to return a 403 with an explanatory message instead of an HTML redirect, so that API clients get a machine-readable error.
46. As a User who has been added to a Team, I want to reach the app normally on my next request, so that no logout/login cycle is needed after being assigned.
47. As an existing advisor, I want all existing Clients, Assessments, Reports, Feedback and PDFExports to belong to "Peak Performance Partners" after the release, so that nothing I could see before disappears.
48. As an existing User (superusers included), I want to be in "Peak Performance Partners" automatically after the release, so that I'm not locked out on deploy day.
49. As a developer setting up a fresh environment, I want the migrations to create no Team on an empty database, so that a business-specific name doesn't leak into fresh environments and tests.
50. As a developer, I want the data migration to fail loudly if Team-owned rows exist but there are no Users, so that a broken backfill never ships silently.
51. As a developer, I want `generate_test_assessment` to accept `--user`, defaulting to the earliest superuser, so that the Assessment it creates has a Created By.
52. As a developer adding a new view, I want a clear, greppable pattern for Team-scoped lookups, so that I know how to avoid leaking data.

## Implementation Decisions

**New `teams` app**

- `Team` model (inherits the project `BaseModel`): `name` only. Registered in Django admin.

**Schema changes**

- `User.team`: FK to Team, nullable, `on_delete=PROTECT`. Exposed on the User admin form.
- `Client.team`: FK to Team, NOT NULL, `on_delete=PROTECT`.
- `created_by`: FK to User, NOT NULL, `on_delete=PROTECT`, on `Client`, `Assessment`, `Feedback`, `PDFExport`. Not on Analysis or any generated Report content, CategoryGuidance, Answer or ClientAccessLink.
- No `team` field on any model other than Client (ADR 0013).

**Migrations** (shipped in one release, three steps)

1. Create `Team`; add `User.team`, `Client.team` and the four `created_by` fields, all nullable.
2. Data migration:
   - If any User or any Team-owned row (Client, Assessment, Feedback, PDFExport) exists: create Team "Peak Performance Partners"; set every existing User's `team` to it (superusers included); set every Client's `team` to it.
   - Pick the backfill User: earliest-created superuser, else earliest-created User. Set `created_by` to it on every existing Client, Assessment, Feedback and PDFExport.
   - If Team-owned rows exist but no User exists, raise with a clear message.
   - On an empty database, do nothing.
   - Reverse operation: null out the fields populated in the forward step (do not delete the Team).
3. Alter `Client.team` and all four `created_by` fields to NOT NULL. `User.team` stays nullable.

**Scoping (ADR 0013)**

- Each Team-owned model gets a custom queryset/manager method `for_team(team)`:
  - Client: `team=team`
  - Assessment: `client__team=team`
  - Analysis, Feedback, PDFExport, ClientAccessLink: `assessment__client__team=team`
- Every view that looks up a Team-owned object does so through `for_team(request.user.team)` and raises 404 when it's absent. A small view mixin/helper may wrap this, but the lookup must remain explicit.
- Views to scope: Client list/create/detail/update; Assessment detail, start (including validating the posted Client), answer, guidance, mark complete, ClientAccessLink generate/revoke/regenerate; Report view, submit feedback, update assessment name, trigger PDF export, PDF export status, trigger analysis, analysis status; PDF template view (logged-in path only); home view counts; the API Client create endpoint.
- The Assessment start form's Client queryset is constructed with the requesting User's Team.
- The Client form excludes `team`; Client creation (UI and API) stamps `team = request.user.team` and `created_by = request.user`. Assessment, Feedback and PDFExport creation stamp `created_by = request.user`.
- AssessmentTemplate, Category, Question and QuestionOption remain global and unscoped.
- Celery tasks (`run_analysis`, `generate_pdf_export`) and beat sweeps remain Team-agnostic; they act only on pks handed to them by already-scoped views.

**Site-wide login**

- Enable Django's `LoginRequiredMiddleware` (Django 6.0).
- Opt out explicitly (`login_not_required`) for: allauth account views (login, signup, password reset, email confirmation, etc.), the client portal views, and the PDF template view (which keeps its own logic: signed-token path is public and Team-agnostic; logged-in path is Team-scoped). Static/media in development as needed.
- The API keeps its DRF authentication; ensure the middleware doesn't break token-authenticated API requests (opt out the API routes from the middleware and rely on DRF's `IsAuthenticated`, which is already the default).

**No-team gate**

- New middleware placed after `LoginRequiredMiddleware`. For an authenticated User with `team is None`:
  - Requests to `/api/` → 403 JSON with an explanatory message.
  - All other requests → redirect to the no-team page, except: the no-team page itself, allauth account pages, Django admin, the client portal, the PDF template view, static and media.
- No-team page: login-required, static copy ("Your account isn't assigned to a team yet. Ask an administrator to add you."), the User's email, a logout button.
- Navbar: when the User has a Team, show the Team name and the Clients/Assessments links. When they don't, hide the Team name and those links; show only My Profile and logout. No Admin link.

**PDF download**

- New Team-scoped download view (e.g. `reports:pdf_download`, keyed by PDFExport pk) that looks up the export via `for_team`, 404s if absent or not complete, and streams the file with `FileResponse` as an attachment using the existing friendly filename.
- The PDF export status endpoint and Report template use this view's URL instead of `export.file.url`.
- Production must stop serving the PDF export media directory publicly. Check how production serves `MEDIA_URL` today; if it is served directly by the web server/static handler, exclude the PDF exports path (or move PDF exports to a non-public storage location). Record what was changed in the issue.

**Admin**

- Team admin: name.
- User admin: Team field (form + list column + list filter).
- Client admin: Team list column + list filter; `created_by` list column; Team editable.
- Assessment, Feedback, PDFExport admin: `created_by` list column.

**Management command**

- `generate_test_assessment` gains `--user` (email); default is the earliest-created superuser; error clearly if none exists. Used as the Assessment's `created_by`.

## Testing Decisions

- Good tests here exercise external behavior only: issue an HTTP request as a given User and assert on status code, redirect target, and rendered/JSON content. They do not assert on queryset internals, middleware ordering, or which helper performed the lookup.
- **Primary seam — Django test client over HTTP.** For each Team-scoped view: a member of the owning Team gets the normal response; a member of another Team gets 404; an anonymous user is redirected to login; a User with no Team is redirected to the no-team page. Creation views assert the created record's `team`/`created_by` via the resulting page or a follow-up request, or a direct model read where that is the only observable effect.
  - Lists/counts: create data for two Teams, assert only the requesting Team's data appears (Client list, Client detail's Assessments, home counts, start-form Client dropdown).
  - Gate: no-team redirect for app pages; admin, account pages, client portal and PDF signed-token path not redirected; `/api/` returns 403 JSON.
  - Login middleware: Client pages redirect anonymous users; allauth and client portal pages remain public.
  - PDF download: owning Team gets the file with attachment disposition and friendly filename; other Team 404; anonymous redirected.
  - API Client create: stamps Team and Created By; no-team User gets 403.
- **Second seam — `call_command`** for `generate_test_assessment --user` (and its default).
- **Data migration**: no automated test; verified manually by running the migrations against a copy of production data before release.
- Factories: `UserFactory` gains a Team (via a `TeamFactory`), `ClientFactory` derives `team` from its `created_by`'s Team; `AssessmentFactory` sets `created_by`. Add Feedback/PDFExport/Analysis factories where tests need them. Existing tests that log in a User must keep passing because the default factory User has a Team.
- Prior art: `reports/tests/test_report_view.py` (logged-in client, `force_login`, redirect for unauthenticated), `client_portal/tests.py` (public token-gated views), `assessments/test_generate_test_assessment_command.py` (`call_command`).

## Out of Scope

- Users belonging to more than one Team, or a Team switcher.
- Roles or permissions within a Team; per-User visibility based on Created By.
- In-app Team management or self-service invitations.
- Per-Team AssessmentTemplates, Categories or Questions.
- Cross-Team visibility for platform admins anywhere other than Django admin.
- Displaying Created By anywhere in the app UI.
- Automated tests for the data migration.
- Scoping Celery tasks or beat sweeps.

## Further Notes

- Glossary: `CONTEXT.md` → Team, Created By, and the updated Key Relationships and PDFExport entries.
- Decision record: `docs/adr/0013-team-scoping-via-client-root-and-explicit-querysets.md`.
- The missing login checks on the Client pages and the public PDF media URLs are existing security gaps; this release closes both, so it's worth calling out in release notes.
- Off-boarding: because every `created_by` is PROTECT, Users who have created records can only be deactivated, never deleted.
