Status: complete

# Report view and template

## Parent

PRD: `.scratch/003-structured-category-sections/PRD.md`

## What to build

Update the report view and template to render the new `ExecutiveSummary` and `CategorySection` models. The view currently passes a single `sections` list to the template; replace this with two separate context variables: `executive_summary` (a single `ExecutiveSummary` instance or `None`) and `category_sections` (a list of `CategorySection` instances ordered by category name).

The template renders the Executive Summary first as the top section of the report, followed by each `CategorySection`. Within each `CategorySection`, render three sub-sections with subheadings: Overview, Impact, and Path Forward. No new cards, colours, or collapsible UI — the only structural change is the subheadings and the Executive Summary appearing at the top.

Update both the `ReportView` and `SubmitFeedbackView` context builders (`_assemble_report` and `get_context_data`) to use `latest_category_sections` and `latest_executive_summary` instead of `latest_sections_by_category`. Update the feedback view to reference `report_feedback` instead of `overall_text` in form handling.

Update all view and template tests to match the new context variable names and rendered structure.

## Acceptance criteria

- [x] Report page renders the Executive Summary as the first section
- [x] Each category is rendered with Overview, Impact, and Path Forward subheadings
- [x] `executive_summary` and `category_sections` are the context variables (not `sections`)
- [x] The report view handles `executive_summary=None` gracefully (no crash when no Analysis has run yet)
- [x] Feedback form continues to work; `report_feedback` field is correctly read and written
- [x] No references to `ReportSection`, `sections` (as the combined list), or `latest_sections_by_category` remain in views or templates
- [x] All view and template tests pass

## Blocked by

- `04-orchestrator-wire-models-queries-ai-service.md`
