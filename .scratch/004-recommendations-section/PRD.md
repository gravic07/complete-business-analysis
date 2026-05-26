Status: ready-for-agent

# PRD: Recommendations Section

## Problem Statement

The current Report gives clients a thorough analysis of their business across seven categories — what their situation is, what impact it has, and what broadly needs to change — but stops short of telling them what to actually do. The CategorySection's Path Forward sub-section gestures at improvement, but it is diagnostic rather than prescriptive. Clients leave the report with a clear picture of their problems and no concrete action list. Advisors must supply recommendations verbally or through a separate document, creating inconsistency across engagements.

## Solution

Add a Recommendations section to every Report. The section opens with a RecommendationsOverview — a short, action-focused synthesis that orients the client to where their biggest gaps are and which areas need the most attention. Following the overview, each of the seven categories receives exactly 7 specific, actionable recommendations. Recommendations are informed by both the Q&A answers and the corresponding CategorySection content, so they follow naturally from the analysis the client just read. The balance of recommendations is calibrated to category performance: high-scoring categories emphasise what to continue; lower-scoring categories emphasise what to start and stop — but every category receives all three types of guidance. The section appears after all CategorySections in the report, so the client understands their situation before receiving action items.

## User Stories

1. As a client reading a Report, I want to see a dedicated Recommendations section, so that I leave the report with specific actions rather than just an understanding of my current state.
2. As a client reading a Report, I want the Recommendations section to open with an overview, so that I understand my biggest priorities before reading the individual category lists.
3. As a client reading a Report, I want the overview to be action-focused rather than analytical, so that it reads as a call to action rather than a recap of the analysis I just finished reading.
4. As a client reading a Report, I want to see exactly 7 recommendations for each category, so that the guidance is specific and actionable without being overwhelming.
5. As a client reading a Report, I want recommendations for every category, regardless of how well I scored, so that I always have a complete picture of what to do next in each area of my business.
6. As a client who scored well in a category, I want my recommendations to emphasise what I should continue doing, so that I know which strengths to protect and build on.
7. As a client who scored poorly in a category, I want my recommendations to emphasise what I should start and stop doing, so that I understand what changes will have the greatest impact.
8. As a client reading a Report, I want every set of recommendations to include guidance on what to start, stop, and continue, so that I get a balanced view of each area regardless of my score.
9. As a client reading a Report, I want each recommendation to be concise and self-contained (1-3 sentences), so that I can scan the list and quickly identify which items are most relevant to me.
10. As a client reading a Report, I want recommendations to reference details about my business — such as company size, industry, and number of employees — so that the guidance is tailored to my actual situation.
11. As a client reading a Report, I want recommendations to build on the analysis in the CategorySection for that area, so that each action item is grounded in the assessment findings rather than generic advice.
12. As a client reading a Report, I want recommendations presented as a numbered or bulleted list per category, so that I can easily reference individual items when discussing the report with my advisor.
13. As a client reading a Report, I want the Recommendations section to appear after the analysis sections, so that I understand my current situation before receiving action items.
14. As an advisor delivering a Report, I want each category's recommendations to be generated alongside its CategorySection, so that analysis and recommendations are always in sync after a feedback cycle.
15. As an advisor delivering a Report, I want the RecommendationsOverview to regenerate whenever any CategoryRecommendations changes, so that the overview is never stale relative to the recommendations below it.
16. As an advisor submitting Feedback on a category, I want that category's recommendations to regenerate along with its CategorySection, so that revised analysis automatically produces updated recommendations.
17. As an advisor submitting report-level Feedback, I want all CategoryRecommendations to regenerate along with all CategorySections, so that a full re-analysis produces a fully updated recommendations set.
18. As an advisor reviewing a Report, I want recommendations written in third person referring to the business by name, so that the tone is consistent with the rest of the report.

## Implementation Decisions

### Two new models: `CategoryRecommendations` and `RecommendationsOverview`

**`CategoryRecommendations`**
- Fields: `analysis` FK, `category` FK (non-nullable), `recommendations` JSONField (a list of exactly 7 strings)
- Unique constraint: `(analysis, category)`
- Each recommendation string is 1-3 sentences — complete, self-contained, no sub-fields

**`RecommendationsOverview`**
- Fields: `analysis` FK, `content` TextField
- Unique constraint: `(analysis,)` — one per Analysis run
- Mirrors `ExecutiveSummary` in structure; no sub-fields

### Generation: two new functions in the AI service

**`generate_category_recommendations`**
- Inputs: Q&A answers for the category, the CategorySection text (overview + impact + path_forward assembled), category score, max possible score for that category, business name, optional prior recommendations (list), optional feedback text
- Returns: `list[str]` — exactly 7 items
- Uses tool calling with a `record_category_recommendations` tool, schema: `{recommendations: {type: array, items: string, minItems: 7, maxItems: 7}}`
- Prompt instructs the model to consider what the business should start, stop, and continue — weighting the balance toward continuation for high-scoring categories and toward change for lower-scoring categories — without labeling individual items. Uses score/max ratio to communicate performance qualitatively.
- No raw numeric scores emitted in output; score context passed silently as a performance signal.
- Third person throughout, business name used instead of "you"/"your"

**`generate_recommendations_overview`**
- Inputs: all CategoryRecommendations assembled as `dict[category_name → list[str]]`, all CategoryScores, max possible scores, business name, optional prior content, optional feedback text
- Returns: `str` — approximately 300-500 words
- Uses text completion (not tool calling) — mirrors `generate_executive_summary` pattern
- Prompt instructs action-focused synthesis: orient the client to where the biggest gaps are and what the recommendations collectively aim to address. Forward-looking and prescriptive, not analytical.
- Category scores passed as silent context; model instructed not to cite raw numbers

### Pipeline: two new generation steps in the orchestrator

After the existing CategorySection and ExecutiveSummary steps:

1. For each in-scope category (same scope as CategorySection generation): generate and create a `CategoryRecommendations` record. The CategorySection for that category (from the current assembled state) is passed as context.
2. After all CategoryRecommendations: generate and create a `RecommendationsOverview` from the full assembled CategoryRecommendations set.

Both new steps include the same idempotency checks as the existing steps — skip if the record already exists for this Analysis run.

A helper function assembles CategoryRecommendations into the dict format expected by `generate_recommendations_overview`, mirroring the existing `_build_section_text` helper used for CategorySections.

### Regeneration: same trigger as CategorySection

`CategoryRecommendations` regenerates under exactly the same conditions as its corresponding `CategorySection` — same feedback scope, same in-scope category set. If a category is in scope for re-analysis, it gets a new `CategorySection` and a new `CategoryRecommendations`.

`RecommendationsOverview` regenerates whenever any `CategoryRecommendations` changes — the same trigger pattern as `ExecutiveSummary` relative to `CategorySections`.

### Report assembly: two new query functions

- **`latest_category_recommendations(assessment)`** — returns the latest `CategoryRecommendations` per category across all Analysis runs, ordered by category name. Uses the same DISTINCT ON subquery pattern as `latest_category_sections`.
- **`latest_recommendations_overview(assessment)`** — returns the latest `RecommendationsOverview` across all Analysis runs, or `None`. Mirrors `latest_executive_summary`.

### View and template

The report view passes two additional context variables: `recommendations_overview` (a single `RecommendationsOverview` or `None`) and `category_recommendations` (a list of `CategoryRecommendations` instances).

The template renders the Recommendations section after all CategorySections: first the RecommendationsOverview, then each category's 7 recommendations as a labelled, numbered list. The section is only rendered if a `RecommendationsOverview` exists.

### Migration

A single migration adds both new tables (`CategoryRecommendations` and `RecommendationsOverview`).

## Testing Decisions

Good tests verify observable external behaviour: what records are created, what values they contain, and what the assembled output looks like given specific inputs. Tests do not assert on internal call counts or private helper invocations.

**Modules to test:**

- **`generate_category_recommendations`** — Given Q&A answers, a CategorySection dict, a score, and a stub client, assert the return value is a list of exactly 7 non-empty strings. Use a capturing stub to assert the prompt contains the answer text, the CategorySection content, and instructs third-person voice. Assert the prompt does not emit raw numeric scores in the output mandate. Prior art: existing injectable stub pattern in `test_ai_service.py`.

- **`generate_recommendations_overview`** — Given a dict of category name → recommendations list and a stub client, assert the return value is a non-empty string. Use a capturing stub to assert the prompt contains all category recommendations text and instructs action-focused, forward-looking synthesis in third person. Assert scores appear in the prompt as context but the model is instructed not to cite them. Prior art: existing `generate_executive_summary` tests in `test_ai_service.py`.

- **Report assembly queries** — Given an Assessment with multiple Analysis runs where some categories were re-analysed, assert `latest_category_recommendations` returns exactly one `CategoryRecommendations` per category (the most recent), and `latest_recommendations_overview` returns the most recent `RecommendationsOverview`. Prior art: existing query tests using the DISTINCT ON pattern in `test_report_view.py` and `queries.py`.

- **Orchestrator: creates CategoryRecommendations and RecommendationsOverview** — Integration test: run the task for a new Analysis. Assert one `CategoryRecommendations` record is created per category, each with a `recommendations` list of exactly 7 non-empty strings. Assert one `RecommendationsOverview` record is created with non-empty `content`. Prior art: `test_task_creates_one_report_section_per_category_plus_overall` in `test_report_generation.py`.

- **Orchestrator: partial regeneration** — Integration test: two Analysis runs where the second only regenerates one category. Assert only the in-scope category gets a new `CategoryRecommendations` in the second run; other categories' `CategoryRecommendations` are the same records from the first run. Assert `RecommendationsOverview` is regenerated in the second run. Prior art: `test_second_run_overall_assembled_from_all_categories_including_prior_runs`.

## Out of Scope

- Recommendation-level feedback targeting (e.g., "revise only recommendation 3 for Sales"). Feedback remains at the category level.
- Labeling individual recommendations as "start", "stop", or "continue" — the framing is a generative lens applied through language, not a structural field or UI tag.
- A score threshold that suppresses recommendations for high-scoring categories — all 7 categories always receive recommendations.
- Roadmap integration — the Roadmap section referenced in `roadmap-schema.php` is a separate future feature.
- PDF export, streaming AI responses, or UI styling beyond the new section structure.

## Further Notes

- See [ADR-0006](../../docs/adr/0006-recommendations-generated-per-category-not-as-single-call.md) for the decision to generate recommendations per-category rather than as a single LLM call, and why the legacy `recommendations-schema.php` single-call approach was not carried forward.
- The `recommendations_prompt` in `report-prompts.php` contained a contradictory score threshold ("less than 800") that was walked back by a later clause in the same prompt. This PRD resolves that contradiction: all categories always receive recommendations.
- `CategoryRecommendations` follows the same idempotency guarantee as `CategorySection` — safe to retry the Celery task without duplicating records (ADR-0004).
- The PHP-era `recommendations-schema.php` modelled the overview as `array[string]` (paragraphs). In the Python implementation, `RecommendationsOverview.content` is a single TextField — paragraph breaks are part of the prose, consistent with how `ExecutiveSummary.content` is stored.
