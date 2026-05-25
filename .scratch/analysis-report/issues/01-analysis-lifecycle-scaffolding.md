Status: ready-for-agent

# Analysis lifecycle scaffolding

## Parent

.scratch/analysis-report/PRD.md

## What to build

Add the `Analysis` model with a `status` field (`pending / processing / complete / failed`) and a nullable FK to `Feedback` (null on first run). Wire up a "Run Analysis" button on the Assessment detail page that creates an `Analysis` record in `pending` status and dispatches a Celery task. The task is a stub at this stage — it simply transitions the status to `complete`. The UI displays the current Analysis status and refreshes to reflect changes. If the task raises an exception, status transitions to `failed` and a meaningful error state is shown to the advisor.

This slice establishes the async loop end-to-end (HTTP request → Celery task → status update → UI) so all subsequent slices can plug into it.

## Acceptance criteria

- [ ] `Analysis` model exists with `status`, `assessment` FK, `feedback` FK (nullable), and `total_score` (nullable) fields
- [ ] "Run Analysis" button appears on the Assessment detail page for completed Assessments
- [ ] Clicking the button creates an `Analysis` record in `pending` status and returns immediately (no blocking wait)
- [ ] A Celery task is dispatched and transitions status from `pending → processing → complete`
- [ ] The UI reflects the current status and updates when processing completes (polling or page refresh)
- [ ] If the Celery task fails, status transitions to `failed` and the UI shows an error state with a retry option
- [ ] An Assessment cannot have two Analysis runs in `pending` or `processing` status simultaneously

## Blocked by

None — can start immediately.
