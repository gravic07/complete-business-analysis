Status: ready-for-agent

# Pipeline integration: Roadmap generation step

## Parent

[PRD: Roadmap Section](../PRD.md)

## What to build

Add the Roadmap generation step as the final step of `_run_analysis_work` in the analysis task orchestrator. The Roadmap is generated after both `RecommendationsOverview` and `ExecutiveSummary` are complete, using the assembled state of all CategoryRecommendations and CategorySections at that point in the run.

The step follows the same idempotency pattern as all existing steps: check whether a `Roadmap` already exists for the current Analysis before generating, and skip if it does. This makes the task safe to retry (ADR-0004).

Inputs to `generate_roadmap` are assembled from:
- `latest_category_recommendations(assessment)` — the same query already called earlier in the task for `RecommendationsOverview`
- `latest_category_sections(assessment)` — the same query already called for `ExecutiveSummary`, with each section assembled into text using the existing `_build_section_text` helper

The Roadmap regenerates in every Analysis run without exception — there is no scope narrowing for the Roadmap (no category-level partial regeneration applies to it).

## Acceptance criteria

- [ ] `_run_analysis_work` creates exactly one `Roadmap` record per Analysis run as its final step
- [ ] Integration test: running the analysis task for a new Assessment creates a `Roadmap` with a `months` list of 12 items, each containing non-empty `goals`, `action_items`, and `challenges` lists
- [ ] Integration test: running a second Analysis run (feedback-triggered) creates a new `Roadmap` record; `latest_roadmap` returns the second run's record
- [ ] Integration test: a partial re-analysis (single category feedback) still produces a new `Roadmap` in the new Analysis run
- [ ] Idempotency: if a `Roadmap` already exists for the Analysis (simulated retry), no duplicate record is created
- [ ] The Roadmap generation step does not run before `RecommendationsOverview` and `ExecutiveSummary` are complete

## Blocked by

- [01 — Roadmap model, migration, and query function](./01-roadmap-model-migration-query.md)
- [02 — `generate_roadmap` AI service function](./02-generate-roadmap-ai-service.md)
