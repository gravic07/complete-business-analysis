Status: ready-for-agent

# Feedback form + targeted re-analysis

## Parent

.scratch/analysis-report/PRD.md

## What to build

Add `Feedback` (`assessment` FK, `overall_text` nullable TextField) and `CategoryFeedback` (`feedback` FK, `category` FK, `text` TextField) models.

Add a Feedback form to the Report view: one textarea for overall feedback and one textarea per Category (all optional). A single form submission creates one `Feedback` record and one `CategoryFeedback` record per non-empty category textarea, then triggers a new `Analysis` run referencing the `Feedback` record.

Implement a scope resolver as a pure function module that takes a `Feedback` record and returns the set of Categories to reprocess, applying this rule:

| Feedback given | Categories reprocessed |
|---|---|
| Overall text only | All categories |
| Category feedback only | Only those categories |
| Both | All categories (category-specific text passed as extra context for that category) |

The Celery task reads the scope from the resolver and only creates new `CategoryScore` and `ReportSection` records for in-scope categories. Out-of-scope categories retain their latest existing sections — the Report view assembles the current Plan from the latest section per category as before, so unchanged sections appear alongside regenerated ones automatically.

The scope resolver must be tested in isolation as a pure function (no database required).

## Acceptance criteria

- [ ] `Feedback` model exists with `assessment` FK and nullable `overall_text`
- [ ] `CategoryFeedback` model exists with `feedback` FK, `category` FK, and `text`
- [ ] Feedback form on the Report view has an overall textarea and one textarea per Category; all fields are optional
- [ ] Submitting the form with at least one non-empty field creates `Feedback`, any `CategoryFeedback` records, and a new `Analysis` in `pending` status referencing the `Feedback`
- [ ] Submitting with all fields empty is rejected with a validation error
- [ ] Scope resolver is a standalone pure function covered by unit tests — no database fixtures needed
- [ ] Celery task applies the scope rule: overall feedback present → all categories reprocessed; category-only feedback → only those categories reprocessed
- [ ] Only in-scope categories receive new `CategoryScore` and `ReportSection` records in this Analysis run
- [ ] The assembled Report view reflects the regenerated sections alongside unchanged sections from prior runs
- [ ] An Assessment cannot have two Analysis runs in `pending` or `processing` status simultaneously (same guard as issue 01)

## Blocked by

- .scratch/analysis-report/issues/03-ai-generated-report-first-run.md
