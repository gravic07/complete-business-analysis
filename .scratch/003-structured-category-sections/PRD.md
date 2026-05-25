Status: ready-for-agent

# PRD: Structured Category Sections and Executive Summary Redesign

## Problem Statement

The current `ReportSection` model stores all AI-generated report content — both per-category narratives and the overall section — as a single unstructured `content` text field, distinguished only by whether `category` is null. Category sections have no internal structure: they are free-form narratives that mix current state, impact, and recommendations in whatever order the LLM chooses. This inconsistency makes reports feel uneven across categories and gives clients no reliable landmarks to navigate the document. The "Overall Section" was designed as a sequencing and urgency tool rather than a true synthesis of the report, which means it does not serve as the natural entry point a client expects when opening a business assessment report.

## Solution

Redesign the report content layer so that each category section is structured into three named sub-sections — Overview, Impact, and Path Forward — and the overall section is replaced by an Executive Summary that synthesises the full report into 4-5 cohesive paragraphs. Split the single `ReportSection` model into two purpose-built models (`CategorySection` and `ExecutiveSummary`) that each carry only the fields they actually need. Update the AI service to produce structured output for category sections and a pure synthesis for the Executive Summary.

## User Stories

1. As a client reading a Report, I want each category section to open with an Overview of my current state in that area, so that I immediately understand where my business stands before reading about consequences.
2. As a client reading a Report, I want each category section to include an Impact sub-section, so that I understand how my current state is affecting my business outcomes.
3. As a client reading a Report, I want each category section to close with a Path Forward sub-section, so that I leave each section with a clear sense of what needs to change.
4. As a client reading a Report, I want each sub-section to be 5-8 sentences long, so that the content is thorough enough to be useful without being exhausting.
5. As a client reading a Report, I want the Executive Summary to give me a holistic picture of my business before I read the individual categories, so that I can approach the detail sections with context.
6. As a client reading a Report, I want the Executive Summary to synthesise what the category sections actually say, so that it reads as a coherent introduction rather than a separate analysis.
7. As a client reading a Report, I want the Executive Summary to be 4-5 paragraphs, so that it gives a complete picture without being as detailed as the full category sections.
8. As a client reading a Report, I want the Overview, Impact, and Path Forward sub-sections to be clearly labelled with subheadings, so that I can navigate within a category section at a glance.
9. As a client reading a Report, I want every section to address me directly in second person, so that the report feels like it was written for me rather than about me.
10. As an advisor reviewing a Report, I want each category section to have a consistent three-part structure across all categories, so that I can evaluate and compare sections predictably.
11. As an advisor reviewing a Report, I want the Executive Summary to reflect the current state of all category sections after any feedback cycle, so that the summary is never stale relative to the categories below it.
12. As an advisor submitting Feedback, I want to provide feedback at the category level that causes the entire category section — all three sub-sections — to be regenerated together, so that the Overview, Impact, and Path Forward remain internally consistent after a revision.
13. As an advisor submitting Feedback, I want to provide report-level feedback that applies across all categories, so that I can direct a full re-analysis when the report needs a different tone or framing throughout.
14. As an advisor, I want the `report_feedback` field on Feedback to be clearly named, so that I can distinguish report-wide context from category-specific feedback without ambiguity.

## Implementation Decisions

### Model split: `ReportSection` → `CategorySection` + `ExecutiveSummary`

`ReportSection` is replaced by two distinct models:

**`CategorySection`**
- Fields: `analysis` FK, `category` FK (non-nullable), `overview` TextField, `impact` TextField, `path_forward` TextField
- Unique constraint: `(analysis, category)`
- No `content` field — the three sub-section fields are the complete content

**`ExecutiveSummary`**
- Fields: `analysis` FK, `content` TextField
- Unique constraint: `(analysis,)` — one per Analysis run
- No Overview/Impact/Path Forward fields

The `category=None` sentinel that previously distinguished the overall section is eliminated. `ExecutiveSummary` is a separate model with no FK to `Category` at all.

### Field rename: `Feedback.overall_text` → `Feedback.report_feedback`

The field `overall_text` on the `Feedback` model is renamed to `report_feedback`. The semantics are unchanged: it is nullable report-wide context that, when present, triggers full reanalysis of all categories. The rename removes the now-ambiguous "overall" reference now that "Overall Section" no longer exists as a domain term.

### AI service: `generate_category_section` returns structured dict

`generate_category_section` changes its return type from `str` to a dict with three keys: `overview`, `impact`, and `path_forward`. The LLM is instructed to return valid JSON matching that shape. The function parses and returns the dict; the caller maps the keys to model fields.

The injectable `llm_client` parameter changes accordingly: it receives a prompt string and must return a string that is valid JSON with those three keys. Tests stub this with a function that returns a hardcoded JSON string.

Prior content for reanalysis is passed as three separate strings (`prior_overview`, `prior_impact`, `prior_path_forward`) rather than a single `prior_content` string.

### AI service: `generate_overall_section` → `generate_executive_summary`

`generate_overall_section` is renamed to `generate_executive_summary`. The function signature remains similar (accepts assembled category section text, scores as silent context, optional prior content, optional feedback text, injectable client), but the prompt mandate changes:

- **Old mandate:** execution sequencing, low-hanging fruit, most urgent items
- **New mandate:** pure synthesis — weave the category sections into a coherent holistic picture of the business in 4-5 paragraphs

The function continues to receive assembled category content (not raw Q&A data) and continues to receive scores as silent context with an explicit instruction not to cite raw numbers in output.

When assembling the category content to pass to the executive summary generator, the orchestrator concatenates each `CategorySection`'s three sub-sections into a single text block per category before passing the `category_sections` dict.

### Report assembly: two queries

The single `latest_sections_by_category` query is replaced by two functions:

- **`latest_category_sections(assessment)`** — returns the latest `CategorySection` per category across all Analysis runs, ordered by category name
- **`latest_executive_summary(assessment)`** — returns the single latest `ExecutiveSummary` across all Analysis runs, or `None` if none exists

The report view and the orchestrator both use these two functions to assemble the current report state.

### Orchestrator updates

The task creates `CategorySection` records (with three fields) instead of `ReportSection` records. The `ExecutiveSummary` is created with the result of `generate_executive_summary` instead of `generate_overall_section`. References to `feedback.overall_text` are updated to `feedback.report_feedback`. The idempotency checks are updated to query `CategorySection` and `ExecutiveSummary` respectively.

When assembling prior content for reanalysis, the orchestrator fetches the prior `CategorySection` and passes its three fields separately to `generate_category_section`.

### Template and view context

The report view passes `executive_summary` (a single `ExecutiveSummary` instance or `None`) and `category_sections` (a list of `CategorySection` instances) as separate context variables instead of a single `sections` list. The template renders the Executive Summary first, then each `CategorySection` with subheadings for Overview, Impact, and Path Forward.

## Testing Decisions

Good tests verify observable external behaviour: what comes out given what goes in, and what records exist in the database after an operation. They do not assert on internal call counts or private method invocations.

**Modules to test:**

- **AI service (`generate_category_section`)** — Given Q&A answers, assert the returned value is a dict with `overview`, `impact`, and `path_forward` keys, each a non-empty string. Use a stub client that returns a valid JSON string. Also assert via a capturing stub that the prompt contains the answer text, instructs second person, and contains no numeric score values. Prior art: existing `test_ai_service.py` injectable stub pattern.

- **AI service (`generate_executive_summary`)** — Given a dict of category name → text, assert the prompt contains all category texts. Assert via a capturing stub that the prompt does not contain the old sequencing/urgency mandate language. Assert it instructs second person. Assert scores appear in the prompt but the model is instructed not to cite them. Prior art: existing `generate_overall_section` tests in `test_ai_service.py`.

- **Report assembly queries** — Given an Assessment with multiple Analysis runs, assert `latest_category_sections` returns exactly one `CategorySection` per category (the most recent), and `latest_executive_summary` returns the most recent `ExecutiveSummary`. Prior art: existing `queries.py` and `test_report_view.py`.

- **Orchestrator: creates CategorySection records** — Integration test: run the task for a new Analysis. Assert `CategorySection` records are created with non-empty `overview`, `impact`, and `path_forward` fields. Assert one `ExecutiveSummary` record is created. Prior art: `test_report_generation.py` `test_task_creates_one_report_section_per_category_plus_overall`.

- **Orchestrator: Executive Summary reads assembled state** — Integration test: two Analysis runs where the second only regenerates one category. Assert the `ExecutiveSummary` for the second run was generated from content that includes unchanged categories from the first run. Prior art: `test_second_run_overall_assembled_from_all_categories_including_prior_runs`.

- **Orchestrator: report_feedback field** — Integration test: create a `Feedback` with `report_feedback` text and assert it flows through to the orchestrator as the overall feedback context. Verify the renamed field is used throughout the scope resolution and prompt assembly.

## Out of Scope

- Sub-section-level feedback targeting (e.g., "revise only the Impact sub-section for Sales"). Feedback remains at the category level; the entire category section is regenerated as a unit.
- Any changes to the `Recommendations`, `Roadmap`, or other plan artifacts referenced in `report-prompts.php`. This PRD covers only the `CategorySection` and `ExecutiveSummary` layer.
- UI styling beyond subheadings — the only rendering change is adding Overview, Impact, and Path Forward subheadings within each category section. No new cards, colours, or collapsible sections.
- PDF export or print layout.
- Streaming AI responses.

## Further Notes

- See [ADR-0005](../../docs/adr/0005-split-reportsection-into-categorysection-and-executivesummary.md) for the decision to split `ReportSection` into two models rather than adding nullable fields.
- ADR-0002 (Report as live-assembled view) and ADR-0003 (Executive Summary generated from assembled category content) remain valid — the assembly strategy and generation source are unchanged by this PRD.
- The `unique_together` constraint on `CategorySection` is `(analysis, category)`, preserving the same idempotency guarantee previously held by `ReportSection`.
- The PHP predecessor (`report-prompts.php`) already specified the three-part structure (overview, impact, path forward) in its `analysis_prompt`. This PRD formalises that structure at the data model and AI service layers rather than leaving it implicit in the prompt text.
