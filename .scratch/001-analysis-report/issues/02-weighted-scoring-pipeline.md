Status: ready-for-agent

# Weighted scoring pipeline

## Parent

.scratch/analysis-report/PRD.md

## What to build

Add the `CategoryScore` model (`analysis` FK, `category` FK, `score`, `max_possible_score`). Implement a scoring engine as a pure function module: given an Assessment's answers, compute `sum(selected_option.rank × selected_option.weight)` per Category and roll up to a total. The total is stored on `Analysis.total_score`; per-category results are stored as `CategoryScore` records.

Replace the Celery task stub from the previous slice with a real implementation that calls the scoring engine and persists these records before transitioning status to `complete`. The Assessment/Analysis detail page displays the total score and a per-category score breakdown. Use Python `Decimal` arithmetic throughout — `weight` is a `DecimalField` and floating-point drift must be avoided.

The scoring engine must be tested in isolation as a pure function (no database required).

## Acceptance criteria

- [ ] `CategoryScore` model exists with `analysis`, `category`, `score`, and `max_possible_score` fields
- [ ] Scoring engine is a standalone module that accepts assessment answer data and returns category scores and a total — no ORM calls inside the engine itself
- [ ] Celery task calls the scoring engine and persists `CategoryScore` records and `Analysis.total_score` on completion
- [ ] All scoring arithmetic uses Python `Decimal` (no floats)
- [ ] Assessment/Analysis detail page shows total score and a score breakdown per Category
- [ ] `max_possible_score` per category reflects the highest possible `rank × weight` sum for that category's questions
- [ ] Scoring engine is covered by unit tests using plain data — no database fixtures needed

## Blocked by

- .scratch/analysis-report/issues/01-analysis-lifecycle-scaffolding.md
