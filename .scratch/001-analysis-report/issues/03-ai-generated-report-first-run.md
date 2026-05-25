Status: ready-for-agent

# AI-generated Report (first run)

## Parent

.scratch/analysis-report/PRD.md

## What to build

Add the `ReportSection` model (`analysis` FK, `category` FK nullable — null means the overall section, `content` TextField). Implement an AI service module that accepts question/answer content and scores for a given scope and returns generated narrative text. The service must use `Answer.question_snapshot` and `Answer.option_snapshot` rather than live `Question`/`QuestionOption` records, so that re-analysis months later reflects what the client actually answered.

Extend the Celery task to call the AI service once per Category plus once for the overall section, storing each result as a `ReportSection` record. `ReportSection` records are never updated after creation.

Add a Report view that assembles the current Report for an Assessment by querying the latest `ReportSection` per Category (plus overall) across all Analysis runs. The view displays the overall section first, followed by one section per Category. Link to the Report from the Client detail page and list prior Analysis runs on the Assessment detail page so advisors can see how the Plan has evolved.

## Acceptance criteria

- [ ] `ReportSection` model exists with `analysis`, `category` (nullable), and `content` fields
- [ ] AI service is a standalone module that accepts plain data (question/answer text, scores, optional feedback) and returns generated text — no direct ORM calls inside the service
- [ ] AI service uses `question_snapshot` and `option_snapshot` fields from `Answer`, not live Question/QuestionOption records
- [ ] Celery task generates one `ReportSection` for the overall plan and one per Category
- [ ] `ReportSection` records are never modified after creation
- [ ] Report view assembles the latest `ReportSection` per Category across all Analysis runs for the Assessment
- [ ] Report view displays: overall section, then one section per Category in order
- [ ] Client detail page links to the assembled Report for each Assessment
- [ ] Assessment detail page lists all Analysis runs with timestamps and status
- [ ] Report view is accessible only to authenticated advisors

## Blocked by

- .scratch/analysis-report/issues/02-weighted-scoring-pipeline.md
