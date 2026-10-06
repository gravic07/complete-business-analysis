# 07 — Scope Reports, Analysis and PDF exports to the Team

**What to build:** Advisors can only read and act on their own Team's Reports, Analysis runs, Feedback and PDFExports. Add `for_team(team)` on Analysis, Feedback and PDFExport (via `assessment__client__team`) and route every lookup through them — or through `Assessment.for_team` where the view keys off an Assessment — with a 404 on miss (ADR 0013). Covers: the Report page, Submit Feedback, Update Assessment Name, Trigger Analysis (including its Feedback lookup), Analysis status, Trigger PDF export, PDF export status, and the Analysis count on the home page. The PDF template page is scoped to the requesting User's Team on its logged-in path; its signed-token path (used by the background PDF renderer) stays Team-agnostic. Celery tasks and beat sweeps are not changed. See PRD § Scoping; user stories 22, 23, 39, 40.

If ticket 06 hasn't landed yet, this ticket adds `Assessment.objects.for_team` itself (same definition: `client__team=team`); whichever lands second reuses it.

**Blocked by:** 01 — Site-wide login required; 03 — Client Team ownership and Created By.

**Status:** ready-for-agent

- [ ] `for_team(team)` exists on Analysis, Feedback and PDFExport and returns only records whose Client belongs to that Team.
- [ ] The Report page, Submit Feedback, Update Assessment Name, Trigger Analysis and Trigger PDF export return 404 for another Team's Assessment and change nothing.
- [ ] Trigger Analysis rejects a Feedback belonging to another Team.
- [ ] Analysis status and PDF export status return 404 for another Team's Analysis/PDFExport.
- [ ] The PDF template page returns 404 to a logged-in User from another Team, renders for the owning Team, and still renders for a valid signed token with no login.
- [ ] The home page Analysis count reflects only the requesting User's Team.
- [ ] PDF export generation end to end still works for the owning Team.
- [ ] Tests (Django test client) set up data for two Teams and cover each of the above.
- [ ] Full test suite passes.
