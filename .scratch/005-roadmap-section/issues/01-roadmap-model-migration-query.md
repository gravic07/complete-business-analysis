Status: ready-for-agent

# Roadmap model, migration, and query function

## Parent

[PRD: Roadmap Section](../PRD.md)

## What to build

Add the `Roadmap` Django model to the `reports` app, create its migration, and add a `latest_roadmap(assessment)` query function following the same pattern as `latest_recommendations_overview` and `latest_executive_summary`.

The model belongs to one Analysis run (unique FK) and stores all generated content as JSON:

- `months` — list of 12 objects, each with `goals`, `action_items`, and `challenges` (each a list of strings)
- `potential_challenges` — list of strings (one string per paragraph)
- `post_implementation_outcomes` — list of strings (one string per paragraph)
- `closing_reflections` — list of strings (one string per paragraph)

The static Overview is not stored — it will live in code as a constant and is not part of this model.

The `latest_roadmap(assessment)` query returns the most recent `Roadmap` for an Assessment across all Analysis runs, or `None` if none exists yet. It mirrors the existing `latest_recommendations_overview` function in `reports/queries.py`.

## Acceptance criteria

- [ ] `Roadmap` model exists in the `reports` app with `analysis` FK (unique), `months` JSONField, `potential_challenges` JSONField, `post_implementation_outcomes` JSONField, and `closing_reflections` JSONField
- [ ] Migration created and applies cleanly
- [ ] `latest_roadmap(assessment)` query function returns the most recent `Roadmap` for an Assessment, or `None`
- [ ] Given an Assessment with two Analysis runs each producing a `Roadmap`, `latest_roadmap` returns the record from the second run
- [ ] `Roadmap` appears in the `reports` app model layout consistent with `ExecutiveSummary` and `RecommendationsOverview`

## Blocked by

None — can start immediately
