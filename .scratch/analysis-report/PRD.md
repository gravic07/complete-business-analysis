Status: ready-for-agent

# PRD: Analysis & Report generation with AI-driven plans and feedback refinement

## Problem Statement

Advisors can submit Assessments on behalf of clients, but there is no way to turn those Assessment answers into actionable plans. The scoring fields (`rank`, `weight`) on `QuestionOption` are unused, the `analysis` and `reports` apps are empty, and there is no workflow for an advisor to receive, review, or refine AI-generated recommendations. Clients are assessed but never given a plan.

## Solution

Build the Analysis and Report pipeline end-to-end:

1. An advisor triggers an Analysis on a completed Assessment
2. The system computes weighted scores per category and in total, then calls an AI to generate a Plan — an overall narrative plus a section per Category — using the full question and answer content as context
3. The assembled Report is displayed to the advisor: one overall section and one section per Category
4. The advisor can submit Feedback (overall, per-category, or both) to trigger a new Analysis run that regenerates only the sections with feedback
5. This cycle repeats until the advisor is satisfied with the Plan

## User Stories

1. As an advisor, I want to trigger Analysis on a completed Assessment, so that a Plan is generated for my client
2. As an advisor, I want to see a status indicator while Analysis is processing, so that I know the system is working and do not need to wait on a blocking page
3. As an advisor, I want to see a total score for an Assessment, so that I can quickly gauge overall business health at a glance
4. As an advisor, I want to see a score breakdown per Category, so that I can identify which areas of the business are strongest and weakest
5. As an advisor, I want to see an overall narrative section in the Report, so that I can understand the high-level strategic recommendations
6. As an advisor, I want to see a dedicated Plan section per Category in the Report, so that I can review targeted recommendations for each area of the business
7. As an advisor, I want to submit overall Feedback on a Report, so that I can guide the AI to adjust the entire Plan
8. As an advisor, I want to submit Feedback on a specific Category section, so that I can refine one area without regenerating the whole Plan
9. As an advisor, I want to submit both overall and per-category Feedback in a single form submission, so that I do not have to trigger multiple Analysis runs for one round of edits
10. As an advisor, I want the re-analysis to regenerate all category sections when overall Feedback is given, so that the AI can apply my strategic direction holistically
11. As an advisor, I want unchanged Category sections to remain intact when only category-specific Feedback is given, so that re-analysis is fast and does not overwrite sections I am satisfied with
12. As an advisor, I want to see the history of Analysis runs for an Assessment, so that I can understand how the Plan has evolved through the feedback cycle
13. As an advisor, I want each Analysis run to record which Feedback it was responding to, so that I can audit why a particular version of the Plan looks the way it does
14. As an advisor, I want the system to handle Analysis failures gracefully and show a meaningful error state, so that I know when to retry rather than waiting indefinitely
15. As an advisor, I want to view the assembled Report for a client from the Client detail page, so that I have a single place to access all client outputs
16. As a client, I want a Plan that references the specific questions and answers from my Assessment, so that the recommendations are grounded in my actual business situation rather than generic advice

## Implementation Decisions

### Models

**`analysis` app**

- `Analysis` — belongs to one Assessment, optionally references one Feedback (null on the first run). Stores `status` (pending / processing / complete / failed), `total_score` (set on completion). One Assessment can have many Analysis runs.
- `CategoryScore` — one record per Category per Analysis run. Stores `score` and `max_possible_score`. Enables per-category display and cross-Assessment trend queries.

**`reports` app**

- `ReportSection` — the atomic output unit. Belongs to one Analysis, covers one Category (nullable = overall section). Stores AI-generated `content` as text. Never updated after creation.
- `Feedback` — belongs to one Assessment (not a specific Report snapshot). Has optional `overall_text`. Has related `CategoryFeedback` records.
- `CategoryFeedback` — one record per Category the advisor comments on. Belongs to one Feedback.

### Scoring formula

`score = sum(selected_option.rank × selected_option.weight)` for all answers in a Category. Total score is the sum of all Category Scores. Scores are computed from live Answer records (not snapshots) but stored on Analysis for display without recomputation.

### Scoring engine

A pure function module that takes an Assessment and returns computed scores by category and total. No side effects. Accepts the list of answers and their selected options. Designed so it can be called from a Celery task and tested in isolation without the full Analysis pipeline.

### Reanalysis scope resolver

A pure function module that takes a Feedback record and returns the set of Categories to reprocess. Rule:
- Overall feedback present → all categories
- Category feedback only → only those categories
- Both → all categories (with category-specific feedback provided per category as additional context)

### AI service

A module that accepts: question/answer content for a set of categories, scores, and any feedback text. Builds a prompt and calls the configured LLM. Returns generated narrative text per section. Decoupled from models — receives plain data, returns plain text. This allows the prompt and model to be iterated without touching the Analysis orchestration logic.

### Analysis orchestrator

Coordinates the full Analysis run: compute scores, resolve reanalysis scope, call the AI service per section, persist CategoryScore and ReportSection records, update Analysis status. Runs inside a Celery task so the HTTP request returns immediately after creating the Analysis record in `pending` status.

### Report assembly

The assembled Report for an Assessment is the latest ReportSection per Category (plus overall) across all Analysis runs. This is a query-time assembly — no single Report model exists. A helper that returns the current Report for an Assessment should be a standalone queryable unit.

### Reanalysis scope rule

| Feedback given | Categories reprocessed |
|---|---|
| Overall only | All categories |
| One or more categories only | Only those categories |
| Overall + categories | All categories (category-specific text passed as extra context for that category) |

### Async processing

Analysis is dispatched as a Celery task immediately after the Analysis record is saved. The UI polls or refreshes to detect status changes. No synchronous AI calls on the request thread.

### Triggering Analysis

The first Analysis on an Assessment is triggered explicitly by the advisor (a button on the Assessment detail page). Subsequent Analysis runs are triggered by Feedback form submission.

## Testing Decisions

Good tests verify external behaviour — inputs and outputs at a module boundary — not internal implementation steps. They do not assert on how many times a function was called internally, what order private methods ran, or which ORM queries were issued.

**Modules to test:**

- **Scoring engine** — given a set of answers with known rank and weight values, assert the correct category scores and total are returned. No database needed; pass in plain data structures.
- **Reanalysis scope resolver** — given Feedback with various combinations of overall text and CategoryFeedback records, assert the correct set of categories is returned. Pure function, no database needed.
- **Report assembler** — given multiple Analysis runs with overlapping ReportSection categories, assert the assembler returns the latest section per category. Requires database fixtures.
- **Analysis orchestrator / Celery task** — integration test: create an Assessment with answers, trigger the task with a mocked AI service, assert that CategoryScore and ReportSection records are created and the Analysis status transitions to `complete`.
- **Feedback form submission** — given a valid Feedback payload, assert a new Analysis is created in `pending` status and dispatched.

Prior art: the existing `AssessmentEntryForm.save()` uses `transaction.atomic()` and creates multiple related records in one operation — the Analysis orchestrator should follow the same pattern and its integration test should follow the same test structure.

## Out of Scope

- Email or in-app notifications when Analysis completes (v2)
- Per-section feedback structure beyond free text (v2)
- PDF export or print layout of Reports
- Comparison of scores across multiple Assessments or clients
- The advisor editing or overriding AI-generated content directly (only Feedback → re-analysis is supported in v1)
- Rate limiting or quota management for AI API calls
- Streaming AI responses to the UI

## Further Notes

- Answer snapshots (`question_snapshot`, `option_snapshot` on the `Answer` model) were designed to preserve question and option content at submission time. The AI service should prefer snapshot content over live Question/QuestionOption records so that a re-analysis triggered months later reflects what the client actually answered, not a question that may have been edited since.
- The `weight` field on `QuestionOption` is a `DecimalField(max_digits=10, decimal_places=4)` — scoring arithmetic should use Python `Decimal` throughout to avoid floating-point drift.
- See [ADR-0001](../../docs/adr/0001-analysis-stored-as-intermediate-record.md) for why Analysis is stored rather than computed on-the-fly.
- See [ADR-0002](../../docs/adr/0002-report-as-live-assembled-view.md) for why Report is a live assembled view rather than a stored snapshot.
