Status: complete

# Orchestrator: wire models, queries, and AI service

## Parent

PRD: `.scratch/003-structured-category-sections/PRD.md`

## What to build

Update the analysis orchestrator (`tasks.py`) and the report assembly queries (`queries.py`) to use the new models and AI service functions introduced in issues 01, 02, and 03.

**Queries:** Replace `latest_sections_by_category` with two functions: `latest_category_sections(assessment)` returns the latest `CategorySection` per category across all Analysis runs (ordered by category name); `latest_executive_summary(assessment)` returns the single latest `ExecutiveSummary` across all Analysis runs, or `None` if none exists.

**Orchestrator — category sections:** Replace `ReportSection.objects.create(content=...)` with `CategorySection.objects.create(overview=..., impact=..., path_forward=...)`, mapping from the dict returned by `generate_category_section`. When a prior `CategorySection` exists for a category, pass its three fields as `prior_overview`, `prior_impact`, and `prior_path_forward` to `generate_category_section`. The idempotency check queries `CategorySection` instead of `ReportSection`.

**Orchestrator — Executive Summary:** Replace `ReportSection.objects.create(category=None, content=...)` with `ExecutiveSummary.objects.create(content=...)`. Call `generate_executive_summary` instead of `generate_overall_section`. When assembling the `category_sections` dict to pass to the generator, concatenate each `CategorySection`'s three fields into a single text block per category. The idempotency check queries `ExecutiveSummary` instead of `ReportSection`.

**Orchestrator — report_feedback:** Replace all references to `feedback.overall_text` with `feedback.report_feedback` throughout scope resolution and prompt assembly.

Update all integration tests to reference `CategorySection` and `ExecutiveSummary` instead of `ReportSection`, and `report_feedback` instead of `overall_text`.

## Acceptance criteria

- [x] `latest_category_sections(assessment)` returns the latest `CategorySection` per category, ordered by category name
- [x] `latest_executive_summary(assessment)` returns the latest `ExecutiveSummary` or `None`
- [x] The orchestrator creates `CategorySection` records with all three fields populated from the AI service dict
- [x] The orchestrator creates one `ExecutiveSummary` record per Analysis run
- [x] Prior `CategorySection` fields are passed as `prior_overview`, `prior_impact`, `prior_path_forward` on reanalysis
- [x] `ExecutiveSummary` receives a concatenated text block per category when being generated
- [x] `feedback.report_feedback` is used throughout; no references to `overall_text` remain in the orchestrator
- [x] Idempotency: re-running the task against the same Analysis does not create duplicate `CategorySection` or `ExecutiveSummary` records
- [x] Integration test: task creates one `CategorySection` per category and one `ExecutiveSummary`
- [x] Integration test: `ExecutiveSummary` on a partial reanalysis run is assembled from all categories including unchanged ones from prior runs
- [x] Integration test: `report_feedback` text flows through to AI service calls as the report-wide context
- [x] All tests pass; no references to `ReportSection` or `latest_sections_by_category` remain

## Blocked by

- `01-data-model-categorysection-executivesummary.md`
- `02-ai-service-generate-category-section-structured.md`
- `03-ai-service-generate-executive-summary.md`
