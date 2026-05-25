Status: ready-for-agent

# Orchestrator — wire new AI service and fix Overall regeneration

## Parent

[PRD: AI Report Generation Quality](./../PRD.md)

## What to build

Update the analysis orchestrator to use the two new AI service functions from issues 01 and 02, and fix the Overall section regeneration rule.

**Replace `generate_section` calls:**
- Category section generation switches from `generate_section` to `generate_category_section`. Scores are no longer passed.
- Overall section generation switches from `generate_section` to `generate_overall_section`. The assembled category sections (see below) and category scores are passed instead of raw Q&A answers.
- The old `generate_section` function can be removed once the orchestrator no longer calls it.

**Fix the Overall regeneration condition:**
The current condition (`if not analysis.feedback_id or overall_feedback`) means the Overall section is skipped when only category-level Feedback is submitted. The correct rule is: always regenerate the Overall section after all Category sections for the current Analysis run are written, regardless of what type of Feedback triggered the run.

**Share the assembled-Report query:**
The orchestrator needs to fetch the full current state of all Category sections — including sections from earlier Analysis runs that are not in scope for this run — to feed into `generate_overall_section`. This is the same "latest ReportSection per Category" query currently used only in the report view. Extract this query into a shared function (or manager method) callable from both the view and the orchestrator, so the logic is not duplicated.

## Acceptance criteria

- [ ] The orchestrator calls `generate_category_section` (not `generate_section`) for each Category in scope; no scores are passed
- [ ] The orchestrator calls `generate_overall_section` for the Overall section; the assembled current state of all Category sections is passed (not raw Q&A)
- [ ] The Overall section is generated on every Analysis run, not only when `overall_feedback` is present
- [ ] The assembled-Report query lives in one shared location used by both the report view and the orchestrator
- [ ] The old `generate_section` function is removed
- [ ] Integration test: run the orchestrator for an Analysis with category-only Feedback (no `overall_text`); assert a ReportSection with `category=None` is created
- [ ] Integration test: set up a first Analysis run that produces sections for all categories; run a second Analysis that only regenerates one category; assert the Overall section for the second Analysis was generated with content from all categories, including unchanged ones from the first run

## Blocked by

- [Issue 01 — AI Service: category section generation](./01-ai-service-category-section.md)
- [Issue 02 — AI Service: overall section generation](./02-ai-service-overall-section.md)
