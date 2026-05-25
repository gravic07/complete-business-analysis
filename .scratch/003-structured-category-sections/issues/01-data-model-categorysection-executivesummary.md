Status: ready-for-agent

# Data model: CategorySection, ExecutiveSummary, report_feedback

## Parent

PRD: `.scratch/003-structured-category-sections/PRD.md`

## What to build

Replace the `ReportSection` model with two purpose-built models: `CategorySection` and `ExecutiveSummary`. Rename `Feedback.overall_text` to `report_feedback`.

`CategorySection` stores the three structured sub-sections for one category within one Analysis run. It has a non-nullable FK to `Category` and three TextFields: `overview`, `impact`, and `path_forward`. Its unique constraint is `(analysis, category)`.

`ExecutiveSummary` stores the top-level synthesis for one Analysis run. It has no FK to `Category` — it belongs only to an `Analysis`. It has a single `content` TextField and a unique constraint on `(analysis,)`.

`Feedback.overall_text` is renamed to `report_feedback`. Semantics are unchanged: nullable report-wide context that triggers full reanalysis when present.

Create the necessary migrations. Update the Django admin to register `CategorySection` and `ExecutiveSummary` and unregister `ReportSection`. Update any test scaffolding, factories, or imports that reference `ReportSection` or `overall_text` so the test suite compiles and passes after the model changes.

## Acceptance criteria

- [ ] `CategorySection` model exists with `analysis` FK, `category` FK (non-nullable), `overview`, `impact`, and `path_forward` TextFields, and `unique_together = [["analysis", "category"]]`
- [ ] `ExecutiveSummary` model exists with `analysis` FK, `content` TextField, and `unique_together = [["analysis"]]`
- [ ] `ReportSection` model is removed
- [ ] `Feedback.report_feedback` field exists (nullable TextField); `overall_text` field is removed
- [ ] Migrations run cleanly from a clean state (`migrate --run-syncdb` passes)
- [ ] Django admin registers `CategorySection` and `ExecutiveSummary`
- [ ] No references to `ReportSection` or `overall_text` remain in model files, admin files, or migration files
- [ ] Test suite passes (stubs or skips for any tests that depend on downstream AI service or orchestrator work not yet done in this issue)

## Blocked by

None — can start immediately.
