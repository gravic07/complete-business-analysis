Status: ready-for-agent

# RecommendationsOverview end-to-end

## Parent

PRD: `.scratch/004-recommendations-section/PRD.md`

## What to build

Add a `RecommendationsOverview` model, generate the top-level overview after all CategoryRecommendations are written, and render it as the opening of the Recommendations section in the Report. This slice completes the Recommendations section by adding the action-focused synthesis that orients the client before they read the per-category lists.

**Model.** `RecommendationsOverview` belongs to one `Analysis`. It stores the overview as a single `content` TextField. Unique constraint: `(analysis,)`. Add the corresponding migration. Mirrors `ExecutiveSummary` in structure.

**AI service.** Add `generate_recommendations_overview` to the AI service. It receives: all CategoryRecommendations assembled as a dict mapping category name to list of recommendation strings, all CategoryScores, max possible scores, business name, optional prior content (string, for reanalysis), and optional feedback text. It returns a `str` of approximately 300-500 words. Use text completion (not tool calling) — the same pattern as `generate_executive_summary`. Follow the injectable `llm_client` pattern.

The prompt must:
- Write in third person, referring to the business by `business_name`
- Instruct action-focused, forward-looking synthesis: orient the client to where the biggest gaps are and what the recommendations collectively aim to address — prescriptive, not analytical
- Pass all category recommendation lists as context
- Pass category scores as silent context; instruct the model not to cite raw numeric scores in output

**Orchestrator.** After the CategoryRecommendations generation loop in `_run_analysis_work`, add a step to generate and store the `RecommendationsOverview`. Check idempotency first (skip if one already exists for this Analysis). Assemble all CategoryRecommendations into the dict format (using a helper analogous to `_build_section_text`). Call `generate_recommendations_overview` with the assembled recommendations, scores, and business name. Pass prior content from the most recent prior run if one exists, and overall feedback text if present.

**Query.** Add `latest_recommendations_overview(assessment)` to `queries.py`. Returns the latest `RecommendationsOverview` across all Analysis runs, or `None`. Mirrors `latest_executive_summary`.

**View.** Pass `recommendations_overview` (a single `RecommendationsOverview` instance or `None`) to the report template context alongside the existing context variables.

**Template.** Render `recommendations_overview.content` as the opening of the Recommendations section, before the per-category lists added in issue 01. Remove or replace any placeholder comment left by issue 01. The full rendered order is: Executive Summary → Category Sections → Recommendations Overview → per-category Recommendations. If `recommendations_overview` is `None`, suppress the entire Recommendations section header (not just the overview text).

## Acceptance criteria

- [ ] `RecommendationsOverview` model exists with `analysis` FK, `content` TextField, and `unique_together = [["analysis"]]`
- [ ] Migration runs cleanly
- [ ] `generate_recommendations_overview` returns a non-empty string given valid inputs and a stub client
- [ ] Prompt passed to the LLM includes all category recommendation text, instructs action-focused third-person synthesis, and does not instruct the model to emit raw numeric scores
- [ ] `_run_analysis_work` creates one `RecommendationsOverview` record per Analysis run, after all CategoryRecommendations are written
- [ ] Re-running the task on an existing Analysis does not create a duplicate `RecommendationsOverview` (idempotency)
- [ ] Any re-analysis run (partial or full) that produces new CategoryRecommendations also produces a new `RecommendationsOverview`
- [ ] `latest_recommendations_overview` returns the most recent `RecommendationsOverview` across all Analysis runs, or `None` if none exists
- [ ] Report view passes `recommendations_overview` to the template context
- [ ] Report template renders `recommendations_overview.content` before the per-category recommendation lists
- [ ] Recommendations section (header + overview + per-category lists) is suppressed entirely when `recommendations_overview` is `None`
- [ ] Unit tests for `generate_recommendations_overview` (return type, prompt content) using the injectable stub pattern — prior art: `generate_executive_summary` tests in `test_ai_service.py`
- [ ] Integration tests for the orchestrator (creates correct record, idempotency, regenerates after any CategoryRecommendations change)
- [ ] Query tests for `latest_recommendations_overview`

## Blocked by

- `.scratch/004-recommendations-section/issues/01-category-recommendations-end-to-end.md`
