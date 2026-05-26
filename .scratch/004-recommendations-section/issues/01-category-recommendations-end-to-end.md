Status: ready-for-agent

# CategoryRecommendations end-to-end

## Parent

PRD: `.scratch/004-recommendations-section/PRD.md`

## What to build

Add a `CategoryRecommendations` model, generate 7 per-category recommendations during each Analysis run, and render them on the Report after the CategorySections. This slice delivers the full vertical path — from database to rendered output — for the per-category half of the Recommendations section.

**Model.** `CategoryRecommendations` belongs to one `Analysis` and one `Category`. It stores the recommendations as a JSONField containing a list of exactly 7 strings. Unique constraint: `(analysis, category)`. Add the corresponding migration.

**AI service.** Add `generate_category_recommendations` to the AI service. It receives: the category's Q&A answers, the assembled CategorySection text (overview + impact + path_forward), the category score, max possible score for that category, business name, optional prior recommendations (list of strings for reanalysis), and optional feedback text. It returns a `list[str]` of exactly 7 items. Use tool calling with a `record_category_recommendations` tool whose schema enforces `{recommendations: {type: array, items: string, minItems: 7, maxItems: 7}}`. Follow the injectable `llm_client` pattern used by `generate_category_section`.

The prompt must:
- Write in third person, referring to the business by `business_name`
- Instruct the model to consider what the business should start doing, stop doing, and continue doing — with the balance weighted toward continuation for high-scoring categories and toward change for lower-scoring ones — but without labeling individual recommendations
- Pass score context qualitatively (score / max possible ratio as a performance signal); instruct the model not to emit raw numeric scores in output
- Include the full CategorySection text as context so recommendations build on the analysis

**Orchestrator.** After the existing CategorySection generation loop in `_run_analysis_work`, add a second loop over the same in-scope categories. For each category: check idempotency (skip if `CategoryRecommendations` already exists for this analysis + category), fetch the current CategorySection for that category (from the assembled latest state), call `generate_category_recommendations`, and create the `CategoryRecommendations` record. Pass prior recommendations from the most recent prior run if one exists, and combined feedback text using the same pattern as CategorySection.

**Query.** Add `latest_category_recommendations(assessment)` to `queries.py`. Returns the latest `CategoryRecommendations` per category across all Analysis runs, ordered by category name. Use the same DISTINCT ON subquery pattern as `latest_category_sections`.

**View.** Pass `category_recommendations` (list of `CategoryRecommendations` instances) to the report template context alongside the existing context variables.

**Template.** Render the per-category recommendations after all CategorySections. For each category, show the category name as a heading and the 7 recommendations as a numbered list. The Recommendations section is only rendered when `category_recommendations` is non-empty. The RecommendationsOverview (added in the next issue) will be inserted above this content — leave a clear placeholder or comment in the template marking where it will go.

## Acceptance criteria

- [ ] `CategoryRecommendations` model exists with `analysis` FK, `category` FK (non-nullable), `recommendations` JSONField, and `unique_together = [["analysis", "category"]]`
- [ ] Migration runs cleanly
- [ ] `generate_category_recommendations` returns a list of exactly 7 non-empty strings given valid inputs and a stub client
- [ ] Prompt passed to the LLM includes the Q&A answer text, the CategorySection content, and third-person instructions; does not instruct the model to emit raw numeric scores
- [ ] `_run_analysis_work` creates one `CategoryRecommendations` record per category after CategorySections are generated
- [ ] Re-running the task on an existing Analysis does not create duplicate `CategoryRecommendations` records (idempotency)
- [ ] Partial re-analysis (feedback on one category) creates a new `CategoryRecommendations` only for in-scope categories; out-of-scope categories reuse their prior record
- [ ] `latest_category_recommendations` returns exactly one record per category (the most recent across all Analysis runs), ordered by category name
- [ ] Report view passes `category_recommendations` to the template context
- [ ] Report template renders each category's 7 recommendations as a numbered list after all CategorySections
- [ ] Unit tests for `generate_category_recommendations` (return shape, prompt content) using the injectable stub pattern
- [ ] Integration tests for the orchestrator (creates correct records, idempotency, partial regeneration) following prior art in `test_report_generation.py`
- [ ] Query tests for `latest_category_recommendations` following prior art in the existing query tests

## Blocked by

None — can start immediately.
