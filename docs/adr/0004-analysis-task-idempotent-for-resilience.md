# Analysis task is idempotent to support in-place retry of failed runs

The `run_analysis` Celery task checks whether a ReportSection already exists for each `(analysis, category)` pair before generating. If a section exists, it is skipped. This makes the task safe to re-run against the same Analysis record without duplicating already-completed work.

The alternative is to create a new Analysis record on retry (implicit current behavior — an advisor resubmits feedback to trigger a fresh run). This was rejected because: (1) it orphans any ReportSections already written in the failed run, discarding work that may have succeeded; (2) it requires advisor intervention (resubmitting feedback) to recover from what may be a transient infrastructure failure; (3) it pollutes the Analysis history with failed records that are indistinguishable from genuine feedback cycles.

With idempotency, a failed Analysis can be retried by calling `run_analysis.delay(analysis_pk)` against the existing `FAILED` Analysis record. The task resumes from the first missing section. A retry trigger (admin action or UI button) is the expected mechanism — no new Analysis record is created.

## Considered Options

- **Discrete Celery task per category section (chord)** — considered for parallelism; rejected because the primary concern is resilience, not speed. Report generation runs async and advisors poll status, so wall-clock time is not the bottleneck. Celery chord failure handling adds meaningful orchestration complexity for a benefit that is not currently needed.
- **Automatic Celery retry (`autoretry_for`)** — considered; rejected because it restarts from the beginning rather than resuming from the point of failure.
