Status: ready-for-agent

# PRD: Roadmap Section

## Problem Statement

The Report gives clients a thorough analysis of their business and a concrete set of per-category recommendations, but stops short of telling them how to sequence those recommendations over time. Clients leave with a clear picture of what to do but no structured plan for when and in what order to do it. Advisors must manually synthesize a roadmap from the recommendations in a separate conversation, creating inconsistency across engagements and placing the sequencing burden entirely on the advisor rather than the system.

## Solution

Add a Roadmap section as the final layer of every Report. The Roadmap translates the full set of CategoryRecommendations into a sequenced 12-month implementation plan, providing the client with an actionable timeline — not just a list of what to do, but a month-by-month arc of how to get there.

The Roadmap opens with a static three-paragraph Overview that orients the client to what a roadmap is and how to use it. This is followed by 12 Monthly Plans, each containing exactly 5 Goals, 5 Action Items, and 5 Challenges. The months are numbered Month 1 through Month 12 (relative, not calendar-based) and are sequenced intelligently — early months lay foundational groundwork that later months depend on. The Roadmap closes with three analytical sections: Potential Challenges (4–7 paragraphs on implementation obstacles), Post-Implementation Outcomes (4–7 paragraphs on what the business will look like after applying the recommendations), and Closing Reflections (encouragement for ongoing progress and monthly tracking).

## User Stories

1. As a client reading a Report, I want to see a Roadmap section after the Recommendations, so that I have a clear plan for implementing the recommendations over the coming year.
2. As a client reading a Report, I want the Roadmap to open with an explanation of what it is and how to use it, so that I understand the purpose and structure before diving into the monthly plans.
3. As a client reading a Report, I want a 12-month plan broken into individual months, so that the implementation feels manageable rather than overwhelming.
4. As a client reading a Report, I want each month to have exactly 5 Goals, so that I have clear targets without being given an unmanageable list.
5. As a client reading a Report, I want each month to have exactly 5 Action Items, so that I know precisely what steps to take each month.
6. As a client reading a Report, I want each month to have exactly 5 Challenges to anticipate, so that I can prepare for likely obstacles rather than being surprised by them.
7. As a client reading a Report, I want the monthly Goals, Action Items, and Challenges to be concise and specific, so that I can scan them quickly and act on them without needing further interpretation.
8. As a client reading a Report, I want the early months to address foundational areas first, so that later months can build on a stable base rather than requiring simultaneous changes across everything.
9. As a client reading a Report, I want each month to be comprehensive across all business categories, so that I am not ignoring areas of my business for months at a time.
10. As a client reading a Report, I want early months to focus on prerequisite categories when necessary, so that the sequencing is logical rather than arbitrary.
11. As a client reading a Report, I want the Roadmap to be grounded in the specific recommendations made for my business, so that the monthly plans feel tailored to my situation rather than generic.
12. As a client reading a Report, I want to read about the potential challenges of implementing the Roadmap, so that I enter the year with realistic expectations.
13. As a client reading a Report, I want the Potential Challenges section to be thorough and specific, so that I can anticipate real obstacles rather than generic platitudes.
14. As a client reading a Report, I want to read about what my business will look like after applying the recommendations, so that I have a motivating vision of the outcome.
15. As a client reading a Report, I want the Post-Implementation Outcomes section to address each area of weakness specifically, so that I understand how addressing the recommendations will change my business in concrete terms.
16. As a client reading a Report, I want to read an encouraging closing section, so that I leave the report motivated to take action.
17. As a client reading a Report, I want the Closing Reflections to encourage regular progress tracking and monthly review meetings, so that I have a clear accountability structure for working through the Roadmap.
18. As a client reading a Report, I want the Closing Reflections to acknowledge that partial completion is still meaningful progress, so that I do not feel like the plan has failed if every item is not completed on time.
19. As a client reading a Report, I want the Roadmap written in third person referring to my business by name, so that the tone is consistent with the rest of the Report.
20. As an advisor delivering a Report, I want the Roadmap to regenerate automatically whenever any CategoryRecommendations changes, so that the Roadmap is always aligned with the current recommendations without requiring a separate action.
21. As an advisor submitting category-level Feedback, I want the Roadmap to regenerate as a downstream consequence, so that updated recommendations are reflected in a fresh Roadmap.
22. As an advisor submitting report-level Feedback, I want the Roadmap to regenerate along with all CategoryRecommendations, so that a full re-analysis produces a fully updated Roadmap.
23. As an advisor reviewing a Report, I want the Roadmap to appear after the Recommendations section, so that the client reads the analysis and action items before the sequenced implementation plan.

## Implementation Decisions

### New model: `Roadmap`

A single `Roadmap` model belonging to one Analysis run. Fields:

- `analysis` FK (unique — one Roadmap per Analysis run)
- `months` JSONField — list of 12 objects, each with:
  - `goals` — list of exactly 5 strings
  - `action_items` — list of exactly 5 strings
  - `challenges` — list of exactly 5 strings
  - No title field — month number is implicit from array index (index 0 = Month 1)
- `potential_challenges` JSONField — list of 4–7 strings (one string per paragraph)
- `post_implementation_outcomes` JSONField — list of 4–7 strings (one string per paragraph)
- `closing_reflections` JSONField — list of strings (one string per paragraph)

The static Overview is not stored — it is a module-level constant rendered directly by the template.

### Generation: one new function in the AI service

**`generate_roadmap`**

- Inputs: all CategoryRecommendations assembled as `dict[category_name → list[str]]`, all CategorySections assembled as `dict[category_name → str]` (using the existing `_build_section_text` helper), business name
- Returns: a dict matching the Roadmap tool schema — `months`, `potential_challenges`, `post_implementation_outcomes`, `closing_reflections`
- Uses tool calling with a dedicated `record_roadmap` tool. Schema enforces `minItems`/`maxItems: 5` on each monthly sub-array and `minItems: 12, maxItems: 12` on the months array. Paragraph arrays enforce `minItems: 4, maxItems: 7`.
- No prior content parameter — the Roadmap is always generated fresh from the current recommendations and sections.
- No feedback text parameter — the Roadmap has no direct feedback path; changes arrive only through upstream regeneration.
- Uses a dedicated LLM client with `max_tokens=8192` (the model ceiling for `claude-sonnet-4-6`), separate from the shared `_default_llm_client()` which uses 4096. This is the only generation call that requires this elevated limit.
- Third person throughout; business name passed and used in place of "you"/"your".
- Scores are not passed as input — the CategorySection Path Forward content already encodes severity qualitatively.

### Pipeline: one new generation step in the orchestrator

After `RecommendationsOverview` is generated (the current last step), add:

- Check if a `Roadmap` already exists for this Analysis (idempotency guard).
- If not, call `generate_roadmap` with the assembled CategoryRecommendations and CategorySections from the latest state across all Analysis runs.
- Create and save the `Roadmap` record.

The Roadmap step runs at the very end of every Analysis run — after both `RecommendationsOverview` and `ExecutiveSummary`. It always regenerates in every Analysis run, mirroring the `RecommendationsOverview` pattern.

### Regeneration trigger

The Roadmap regenerates in every Analysis run, exactly like `RecommendationsOverview`. Any category or report-level feedback cycle creates a new Analysis run, which always produces a new Roadmap. There is no roadmap-specific feedback mechanism.

### Report assembly: one new query function

**`latest_roadmap(assessment)`** — returns the most recent `Roadmap` for an Assessment across all Analysis runs, or `None`. Mirrors `latest_recommendations_overview`.

### Static Overview template

A module-level constant (three paragraphs) explaining what the Roadmap is and how to use it. Not LLM-generated. Identical for every client. Rendered by the template directly — not stored in the database, not passed through the generation pipeline.

### View and template

The report view passes one additional context variable: `roadmap` (a `Roadmap` instance or `None`).

The template renders the Roadmap section after the Recommendations section. Structure: static Overview text, then 12 monthly plan cards (each showing Month N, then Goals / Action Items / Challenges as labelled lists), then Potential Challenges paragraphs, Post-Implementation Outcomes paragraphs, and Closing Reflections paragraphs. The entire section is only rendered if a `Roadmap` exists.

### Migration

A single migration adds the `Roadmap` table.

## Testing Decisions

Good tests verify observable external behaviour: what records are created, what values they contain, and what the assembled output looks like given specific inputs. Tests do not assert on internal call counts, prompt internals, or private helper structure.

**Modules to test:**

- **`generate_roadmap`** — Given assembled CategoryRecommendations and CategorySections dicts and a stub client, assert the return value contains a `months` list of exactly 12 items, each with `goals`, `action_items`, and `challenges` lists of exactly 5 strings. Assert `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` are non-empty lists. Use a capturing stub to assert the prompt contains the category recommendations text and category section text. Prior art: injectable stub pattern in `test_ai_service.py` and `test_category_recommendations_ai_service.py`.

- **Report assembly query** — Given an Assessment with multiple Analysis runs, assert `latest_roadmap` returns the most recent `Roadmap` record. Prior art: `latest_recommendations_overview` and `latest_executive_summary` query tests.

- **Orchestrator: creates Roadmap** — Integration test: run the task for a new Analysis. Assert exactly one `Roadmap` record is created, with a `months` list of 12 items each containing properly structured sub-lists, and non-empty prose section lists. Prior art: `test_task_creates_one_report_section_per_category_plus_overall` in the analysis task tests.

- **Orchestrator: Roadmap regenerates on every run** — Integration test: two Analysis runs (second triggered by feedback). Assert a new `Roadmap` record is created in the second run. Assert `latest_roadmap` returns the second run's record. Prior art: partial regeneration tests for `RecommendationsOverview`.

- **Orchestrator: idempotency guard** — Integration test: simulate a retry where the Roadmap record already exists for the Analysis. Assert no duplicate Roadmap record is created. Prior art: existing idempotency tests for `ExecutiveSummary` and `RecommendationsOverview`.

## Out of Scope

- Roadmap-specific feedback (e.g., "re-sequence the roadmap without changing recommendations"). The only way to change the Roadmap is through upstream category or report-level Feedback.
- Per-month or per-section partial regeneration of the Roadmap. The Roadmap is always regenerated in full.
- Calendar-anchored months. Months are numbered Month 1 through Month 12 and are relative to the report date, not tied to specific calendar months.
- Thematic month titles. Month numbers are sufficient; the goals and action items communicate the theme.
- PDF export, streaming AI responses, or UI styling beyond rendering the new section structure.
- Advisor ability to mark roadmap items as complete or track progress within the tool.

## Further Notes

- See [ADR-0007](../../docs/adr/0007-roadmap-generated-as-single-llm-call.md) for the decision to generate the Roadmap as a single LLM tool call rather than per-section calls, and why the decomposed pattern from ADR-0006 does not apply here.
- The `roadmap_prompt` in `report-prompts.php` describes a prompt that asked the client to "pick at least five recommendations." That instruction is not carried forward — the Roadmap is generated from the full recommendation set, and prioritization is implicit in the monthly sequencing.
- The `roadmap-schema.php` sketch included a `month_title` field. This PRD drops that field — month identity is implicit from array position, and thematic titles were rejected as adding variability without proportional value.
- `Roadmap` follows the same idempotency guarantee as all other Report artifacts — safe to retry the Celery task without duplicating records (ADR-0004).
