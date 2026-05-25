Status: done

# Orchestrator — task idempotency

## Parent

[PRD: AI Report Generation Quality](./../PRD.md)

## What to build

Make the `run_analysis` Celery task idempotent so a failed Analysis can be retried in-place without creating a new Analysis record.

**Existence check before generation:**
Before generating each Category section, the orchestrator checks whether a ReportSection already exists for that `(analysis, category)` pair. If it does, the section is skipped. The same check applies to the Overall section (`analysis` + `category=None`). This makes re-running the task against the same Analysis record safe — completed sections are preserved and the task resumes from the first missing one.

**Retry semantics:**
A `FAILED` Analysis can be retried by dispatching the existing `run_analysis` Celery task with the same `analysis_pk`. The task transitions the status back to `processing` at the start of each run regardless of its current status, so a retry from `FAILED` is treated the same as a first run — except completed sections are skipped.

No new Analysis record is created on retry. The audit trail for a partial failure is a single Analysis record that transitions `pending → processing → failed → processing → complete`.

## Acceptance criteria

- [x] Before generating each Category ReportSection, the orchestrator checks for an existing `(analysis, category)` ReportSection and skips generation if one is found
- [x] Before generating the Overall ReportSection, the orchestrator checks for an existing `(analysis, category=None)` ReportSection and skips generation if one is found
- [x] Dispatching `run_analysis` with the `pk` of a `FAILED` Analysis transitions its status back to `processing` and resumes generation
- [x] Integration test: run the orchestrator for an Analysis, then call the orchestrator function again for the same Analysis; assert the total number of ReportSections belonging to that Analysis has not increased
- [x] Integration test: simulate a partial failure by creating some ReportSections for an Analysis manually, then run the orchestrator; assert only the missing sections are generated (the pre-existing ones are not regenerated)

## Blocked by

- [Issue 03 — Orchestrator: wire new AI service and fix Overall regeneration](./03-orchestrator-wire-new-ai-service.md)
