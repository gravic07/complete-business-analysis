# 06 — Scope Assessments and ClientAccessLinks to the Team

**What to build:** Advisors can only view and change their own Team's Assessments and ClientAccessLinks. Add `for_team(team)` on Assessment (via its Client's Team) and ClientAccessLink (via its Assessment's Client's Team), and route every lookup through them with a 404 on miss (ADR 0013). Covers: Assessment detail, Answer Questions, Guidance, Mark Complete, ClientAccessLink Generate/Revoke/Regenerate, and the Assessment count on the home page. Client portal access via a ClientAccessLink token stays Team-agnostic and unchanged. See PRD § Scoping; user stories 20, 21, 27, 38.

**Blocked by:** 03 — Client Team ownership and Created By.

**Status:** done

- [x] `Assessment.objects.for_team(team)` and `ClientAccessLink.objects.for_team(team)` return only records whose Client belongs to that Team.
- [x] Assessment detail, Answer Questions, Guidance and Mark Complete return 404 (GET and POST) for another Team's Assessment and work normally for the owning Team.
- [x] Generate, Revoke and Regenerate a ClientAccessLink return 404 for another Team's Assessment and change nothing.
- [x] The home page Assessment count reflects only the requesting User's Team.
- [x] Moving a Client to another Team in admin makes its Assessments visible to the new Team and invisible to the old one.
- [x] Client portal pages reached through a valid token behave exactly as before.
- [x] Tests (Django test client) set up data for two Teams and cover each of the above.
- [x] Full test suite passes.

## Comments

`assessments/models.py` adds `AssessmentQuerySet.for_team(team)` (filters on `client__team`) and `ClientAccessLinkQuerySet.for_team(team)` (filters on `assessment__client__team`), exposed as each model's `objects`. Both follow `ClientQuerySet`: they accept `Team | None`, and `None` matches nothing. No migration is needed.

Views (`assessments/views.py`):
- A module helper `_team_assessments(request)` returns `Assessment.objects.for_team(request.user.team)`. These all look the Assessment up through it, so another Team's Assessment returns 404:
  - `AssessmentDetailView.get_queryset`
  - `AssessmentAnswerView.setup` and `CategoryGuidanceView.setup`
  - `MarkCompleteView.post`
  - `ClientAccessLinkActionView.setup`
- Answer, Guidance and the link actions resolve the Assessment in `setup()`, so GET and POST both 404 before any handler runs. Anonymous requests can't reach `setup()`, because `SiteLoginRequiredMiddleware` stops them in `process_view`.
- `ClientAccessLinkActionView._get_active_link` (Revoke/Regenerate) also goes through `ClientAccessLink.objects.for_team(...)`. It's redundant because the Assessment is already scoped, but it keeps the `get_object_or_404` on links explicit, as ADR 0013 asks.
- The read-only link lookups that feed the detail hub and the Guidance/Answer pages still filter by `assessment=` without `for_team`. The Assessment they filter by was already looked up through `_team_assessments`, so nothing leaks.
- `HomeView`'s Assessment count is scoped. The Analysis count is left to issue 07.

Client portal: unchanged. It still resolves links by token with no Team check. A new test confirms a token still works while another Team's advisor is logged in.

Tests:
- Existing assessment view tests now log in `UserFactory.create(team=assessment.client.team)`, or `link.assessment.client.team` where there is only a link. Many of these tests pass an explicit `client=`, so the creator's Team isn't the Client's Team.
- The admin-move test posts the real Client change form, then checks the detail page as both the old Team and the new Team.

Review notes (not done):
- `_logged_in_client(user)` is now defined in both `assessments/tests.py` and `core/tests.py`. It could become a shared `conftest.py` fixture.
- The admin-move test lists the Client form fields by hand, so it needs updating whenever a required Client field is added.
- The unscoped Assessment, Analysis, Feedback and PDFExport lookups in `reports/views.py` belong to issue 07.
