# 07 — Scope Reports, Analysis and PDF exports to the Team

**What to build:** Advisors can only read and act on their own Team's Reports, Analysis runs, Feedback and PDFExports. Add `for_team(team)` on Analysis, Feedback and PDFExport (via `assessment__client__team`) and route every lookup through them — or through `Assessment.for_team` where the view keys off an Assessment — with a 404 on miss (ADR 0013). Covers: the Report page, Submit Feedback, Update Assessment Name, Trigger Analysis (including its Feedback lookup), Analysis status, Trigger PDF export, PDF export status, and the Analysis count on the home page. The PDF template page is scoped to the requesting User's Team on its logged-in path; its signed-token path (used by the background PDF renderer) stays Team-agnostic. Celery tasks and beat sweeps are not changed. See PRD § Scoping; user stories 22, 23, 39, 40.

If ticket 06 hasn't landed yet, this ticket adds `Assessment.objects.for_team` itself (same definition: `client__team=team`); whichever lands second reuses it.

**Blocked by:** 01 — Site-wide login required; 03 — Client Team ownership and Created By.

**Status:** done

- [x] `for_team(team)` exists on Analysis, Feedback and PDFExport and returns only records whose Client belongs to that Team.
- [x] The Report page, Submit Feedback, Update Assessment Name, Trigger Analysis and Trigger PDF export return 404 for another Team's Assessment and change nothing.
- [x] Trigger Analysis rejects a Feedback belonging to another Team.
- [x] Analysis status and PDF export status return 404 for another Team's Analysis/PDFExport.
- [x] The PDF template page returns 404 to a logged-in User from another Team, renders for the owning Team, and still renders for a valid signed token with no login.
- [x] The home page Analysis count reflects only the requesting User's Team.
- [x] PDF export generation end to end still works for the owning Team.
- [x] Tests (Django test client) set up data for two Teams and cover each of the above.
- [x] Full test suite passes.

## Comments

New querysets, each exposed as the model's `objects`:
- `analysis/models.py` adds `AnalysisQuerySet.for_team(team)`.
- `reports/models.py` adds `FeedbackQuerySet.for_team(team)` and `PDFExportQuerySet.for_team(team)`.

All three filter on `assessment__client__team` and accept `Team | None`, where `None` matches nothing. No migration is needed.

Views (`reports/views.py`):
- A module helper `_team_assessments(request)` returns `Assessment.objects.for_team(...)`, the same pattern as `assessments/views.py`.
- These look the Assessment up through it:
  - `ReportView.get_queryset`
  - `SubmitFeedbackView.setup`
  - `UpdateAssessmentNameView`
  - `TriggerAnalysisView`
  - `TriggerPDFExportView`
- `TriggerAnalysisView`'s Feedback lookup and its retry-Analysis lookup go through `Feedback`/`Analysis.objects.for_team(...)`. Both also still filter by `assessment=`.
- `AnalysisStatusView` and `PDFExportStatusView` look up through `Analysis.objects.for_team` and `PDFExport.objects.for_team`.
- `PDFTemplateView.get_queryset` is Team-scoped when the user is logged in, and uses `Assessment.objects.all()` on the anonymous signed-token path.
  - `dispatch` checks login first, so a logged-in user from another Team who also passes a valid token still gets 404. A test pins this.
- `HomeView`'s Analysis count is scoped.
- Celery tasks and beat sweeps are unchanged.

Tests:
- `reports/tests/test_team_scoping.py` sets up two Teams (`ours`/`theirs`) and covers each criterion.
- The 404 tests also check that nothing changed:
  - no Feedback, Analysis or PDFExport row is created;
  - the other Team's Assessment keeps its name;
  - no task is queued;
  - a retried Analysis keeps its status.
- The end-to-end test runs:
  - the trigger view;
  - the real `generate_pdf_export` task, with Playwright replaced by an anonymous test-client fetch of the same signed-token URL;
  - the status endpoint.
- Existing report view tests now log in a member of the Assessment's Team (`assessment.created_by`, `export.created_by`, or `UserFactory.create(team=assessment.client.team)`).
- `core/tests.py`: the no-Team-user PDF template test is renamed to `..._is_not_redirected_...` and now expects 404 instead of 200.
  - The gate still leaves the page alone, but the logged-in path is Team-scoped (PRD story 40), and `for_team(None)` matches nothing.

Review notes (not done):
- `_team_assessments` is now defined in both `assessments/views.py` and `reports/views.py`. It could become one shared helper.
- The four `for_team` bodies filtering on `assessment__client__team` (including `ClientAccessLink`'s) could share a mixin.
- `reports/views.py` adds a small `_team(request)` helper, while `assessments`/`clients` inline `assert ...; request.user.team`.
- `PDFExportStatusView` still returns the public `export.file.url`, and the end-to-end test asserts it is non-empty. Ticket 08 replaces that URL with a Team-scoped download view and should update that assertion.
