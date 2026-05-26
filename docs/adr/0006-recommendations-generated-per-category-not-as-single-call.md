# ADR-0006: Recommendations generated per-category, not as a single LLM call

## Status
Accepted

## Context
The recommendations section of the Report consists of a top-level RecommendationsOverview and 7 CategoryRecommendations items per category. An earlier PHP-era schema (`recommendations-schema.php`) modelled this as a single LLM call returning `{overview, sections: [{section_title, recommendations}]}`. When porting to the Python codebase, we chose between keeping that single-call approach and following the per-category pattern already established for CategorySections.

## Decision
Generate CategoryRecommendations one category at a time (one LLM call per category), then generate the RecommendationsOverview in a separate call — mirroring the CategorySection + ExecutiveSummary pattern (ADR-0005).

## Consequences
- Partial regeneration works naturally: when feedback targets one category, only that category's CategorySection and CategoryRecommendations are regenerated; unchanged categories are reused from prior runs.
- RecommendationsOverview regenerates whenever any CategoryRecommendations changes — the same trigger pattern as ExecutiveSummary.
- Each CategoryRecommendations call receives focused context: that category's Q&A answers and its current CategorySection text.
- More LLM calls per Analysis run (7 + 1 vs. 1), but consistent with the existing architecture and the idempotency guarantee from ADR-0004.

## Alternatives considered
**Single call:** One LLM call returns overview + all category recommendations together. Simpler and cheaper on the first run, but forces full recommendations regeneration even when feedback only touches one category. Also inconsistent with the per-category architecture that enables the feedback cycle.
