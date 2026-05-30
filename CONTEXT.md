# Domain Context

## Glossary

### Assessment
A completed set of answers submitted by an advisor on behalf of a Client, based on an AssessmentTemplate. An Assessment is the starting point for all analysis. It is immutable once submitted — answers are preserved via snapshots.

### Analysis
A single run of the scoring and AI-generation process against an Assessment. Stored as a persistent record. Inputs include: computed scores (total + per-category), question/answer content, and any Feedback from a prior Report. Produces exactly one Report. An Assessment can have many Analysis runs over its lifetime.

### Report
A live view assembled at render time from the latest ReportSection per Category across all Analysis runs for an Assessment. Not stored as a monolithic document — it is always the most current section per category. Advisors submit Feedback against the Report, which triggers a new Analysis run covering only the categories that received feedback.

**Report audience:** The Report is written in third person, referring to the Client by their business name ("Acme Corp is currently...", "Acme Corp's approach...") — not in second person ("you", "your business"). Advisors review the Report for accuracy before delivering it to the Client and assisting with implementation, but the Client is the intended reader of the final document.

### CategorySection
The atomic unit of a category-level Report. Belongs to one Analysis run and covers one specific Category. Structured as three sub-sections: Overview (current state summary, 5-8 sentences), Impact (how the current state affects the business, 5-8 sentences), and Path Forward (short description of changes needed, 5-8 sentences). When re-analysis runs for a single category, only a new CategorySection is created for that category; unchanged sections from prior Analysis runs are reused.

### ExecutiveSummary
The top-level section of a Report. Belongs to one Analysis run. A pure synthesis of all CategorySections into a coherent holistic picture — 4-5 paragraphs. Does not carry the Overview/Impact/Path Forward structure. Regenerated whenever any CategorySection changes.

### Feedback
Input provided by an advisor after reviewing a Report. Submitted as a single form covering two levels:
- **Report Feedback** (`report_feedback`, nullable) — comments on the Report as a whole. When present, ALL categories are reanalyzed in the next Analysis run, with the report feedback provided as additional context. The AI may change each category to varying degrees.
- **Category Feedback** — one `CategoryFeedback` record per category the advisor comments on (`category` + `text`). When present without report feedback, only those specific categories are reanalyzed.

**Reanalysis scope rule:**
- Report feedback only → all categories reprocessed
- Category feedback only → only commented categories reprocessed
- Both → all categories reprocessed (each category receives both report feedback and its specific feedback if present)

Feedback belongs to an Assessment (not a specific Report snapshot) and triggers one new Analysis run.

### Score
A numeric value computed from an Assessment's answers using a weighted sum formula:

`score = sum(selected_option.rank × selected_option.weight)`

Computed at two layers:
- **Category Score** — the weighted sum for all answers within one Category, stored as a `CategoryScore` record (one per Category per Analysis run). Queryable for trend analysis and cross-Assessment comparison.
- **Total Score** — the sum of all Category Scores, stored directly on the Analysis record.

### CategoryScore
A normalized record storing the computed score for one Category within one Analysis run. Fields: `analysis`, `category`, `score`, `max_possible_score`. Enables filtering and trend queries across Analysis runs.

### Plan
The AI-generated content inside a Report — actionable recommendations derived from the content of questions and answers, not just their scores. Advisors can influence a Plan by submitting Feedback, which produces a new Report. A Plan consists of four distinct layers:

- **Category Section** — a focused analysis of one business area structured as three named sub-sections: Overview (current state summary), Impact (how the current state affects the business), and Path Forward (short description of changes needed). Generated from that category's Q&A answers only.
- **Executive Summary** — a true synthesis of the full report, condensing and stitching together the Category Sections into a coherent holistic picture. Does not carry a sequencing or urgency mandate — those are handled within each Category Section's Path Forward. Generated from the full text of all Category Sections — not from raw Q&A data. Rendered as 4-5 paragraphs with no Overview/Impact/Path Forward structure.
- **Recommendations** — action-focused content generated for every category regardless of score. Consists of a top-level RecommendationsOverview and one CategoryRecommendations record per category. The start/stop/continue framing is a soft generative lens: high-scoring categories emphasise continuation, lower-scoring categories emphasise what to start and stop — but every category receives all three types of guidance. Generated after CategorySections are complete; CategorySection content is used as input context alongside Q&A answers.
- **Roadmap** — a 12-month implementation plan synthesizing all CategoryRecommendations and CategorySections into a sequenced action plan. Generated as a single LLM tool call after all recommendations are complete. The final layer of a Plan.

### RecommendationsOverview
The top-level section that leads the Recommendations portion of a Report. Action-focused — orients the Client to where the business's biggest gaps are and what the recommendations collectively aim to address. Approximately 300–500 words. Does not carry the Overview/Impact/Path Forward structure. Analogous to ExecutiveSummary in scope, but forward-looking and prescriptive rather than synthetic. Regenerated whenever any CategoryRecommendations changes — mirrors the ExecutiveSummary regeneration trigger. Generated from: all CategoryRecommendations text (assembled) + all CategoryScores + business background context.

### CategoryRecommendations
Exactly 7 actionable recommendations for one Category within one Analysis run. Generated for every category regardless of score. Regenerates under exactly the same conditions as its corresponding CategorySection — same feedback scope, same triggers. The start/stop/continue framing is a soft generative lens applied by the model: high-scoring categories will emphasise continuation, lower-scoring categories will emphasise what to start and stop — but all three types of guidance appear in every set. Each recommendation is a single, self-contained, 1–3 sentence item. Not structured with sub-fields per recommendation — the model applies the framing through language, not labeling. Generated from: that category's Q&A answers + its CategorySection text + its CategoryScore + business background context only — no cross-category visibility.

### Roadmap
A 12-month implementation plan synthesized from all CategoryRecommendations and CategorySections for one Analysis run. The final section of a Report. Belongs to one Analysis. Regenerates whenever any CategoryRecommendations changes — mirrors the RecommendationsOverview regeneration trigger. Does not accept feedback of its own; changes only through upstream category or report-level Feedback. Generated fresh each time — no prior version is passed as context.

Structured as five sections:
- **Overview** — Static 3-paragraph template explaining what the Roadmap is and how to use it. Not LLM-generated; identical across all clients.
- **Monthly Plans** — 12 monthly plans numbered Month 1 through Month 12 (relative, not calendar-based). Each contains exactly 5 Goals, 5 Action Items, and 5 Challenges. Months are comprehensive across all categories but may focus a specific category when that category is a prerequisite for later months.
- **Potential Challenges** — 3–4 paragraphs describing obstacles to implementing the roadmap. Stored as a plain string with `\n\n`-separated paragraphs.
- **Post-Implementation Outcomes** — 3–4 paragraphs describing the business after recommendations are applied, with specific reference to each addressed weakness. Stored as a plain string with `\n\n`-separated paragraphs.
- **Closing Reflections** — 4–6 paragraphs encouraging ongoing progress, monthly tracking meetings, and continued iteration even when not all roadmap items are completed. Stored as a plain string with `\n\n`-separated paragraphs.

### Business Profile
Three required fields on a Client that describe the organizational shape of the business — distinct from contact info (`first_name`, `last_name`, `title`) and classification (`industry`):

- **Company Size** — headcount band: 1–4, 5–19, 20–49, 50–100, 101+
- **Revenue** — annual revenue band: $1M or less, $1M–$2.5M, $2.5M–$10M, $10M–$50M, $50M+
- **Corporate Style** — ownership and governance structure: Family-Owned, Sole Proprietorship, Board-governed / Corporate, Partnership

Business Profile fields are injected as qualitative context into category-level generation calls (CategorySection and CategoryRecommendations) only. The ExecutiveSummary and RecommendationsOverview inherit this context implicitly, because they are generated from the outputs of those leaf-level calls — not from raw Client data directly.

### Analysis Status
An Analysis moves through states: `pending → processing → complete` or `pending → processing → failed`. Status is stored on the Analysis record. Processing is handled asynchronously via Celery so the UI can show a processing state without blocking.

## Core Lifecycle

```
Assessment → Analysis → Report → Feedback → Analysis → Report → ...
```

- One Assessment → many Analysis runs (one per feedback cycle)
- One Analysis → exactly one Report
- One Report → zero or one Feedback (which spawns the next Analysis)
- AI drafts the Plan; advisors provide Feedback to refine it

## Key Relationships

- `Client` has many `Assessments`
- `Assessment` has many `Analysis` runs
- `Analysis` belongs to one `Assessment`, optionally references one `Feedback` (null on first run)
- `Analysis` produces many `CategoryScore` records, many `CategorySection` records, one `ExecutiveSummary`, many `CategoryRecommendations` records, one `RecommendationsOverview`, and one `Roadmap`
- `CategorySection` belongs to one `Analysis` and one `Category`
- `ExecutiveSummary` belongs to one `Analysis`
- `CategoryRecommendations` belongs to one `Analysis` and one `Category`
- `RecommendationsOverview` belongs to one `Analysis`
- `Roadmap` belongs to one `Analysis`
- `Feedback` belongs to one `Assessment`, has optional `overall_text` and many `CategoryFeedback` records
- `CategoryFeedback` belongs to one `Feedback` and one `Category`

## Model Layout

### `clients` app
| Model | Key Fields |
|---|---|
| `Client` | `business_name`, `first_name`, `last_name`, `title`, `industry` (choice), `company_size` (choice), `revenue` (choice), `corporate_style` (choice) |

### `analysis` app
| Model | Key Fields |
|---|---|
| `Analysis` | `assessment` FK, `status` (pending/processing/complete/failed), `total_score`, `feedback` FK (nullable) |
| `CategoryScore` | `analysis` FK, `category` FK, `score`, `max_possible_score` |

### `reports` app
| Model | Key Fields |
|---|---|
| `CategorySection` | `analysis` FK, `category` FK, `overview` TextField, `impact` TextField, `path_forward` TextField |
| `ExecutiveSummary` | `analysis` FK, `content` TextField |
| `CategoryRecommendations` | `analysis` FK, `category` FK, `recommendations` JSONField (list of 7 strings) |
| `RecommendationsOverview` | `analysis` FK, `content` TextField |
| `Roadmap` | `analysis` FK, `months` JSONField (list of 12 objects with `goals`, `action_items`, `challenges` — each a list of 5 strings), `potential_challenges` TextField, `post_implementation_outcomes` TextField, `closing_reflections` TextField |
| `Feedback` | `assessment` FK, `report_feedback` (nullable) |
| `CategoryFeedback` | `feedback` FK, `category` FK, `text` TextField |

## Reanalysis Scope Rule
- Report feedback only → all categories reprocessed
- Category feedback only → only commented categories reprocessed
- Both → all categories reprocessed; category-specific feedback provided per category

The ExecutiveSummary regenerates whenever any CategorySection changes — not only when `report_feedback` is present. After all in-scope CategorySections are written, the ExecutiveSummary is always regenerated using the full assembled Report state (latest CategorySection per category across all Analysis runs).

## Prompt Design Rules
- Category section prompts contain no numeric scores — severity is communicated through qualitative answer content only.
- The ExecutiveSummary prompt receives scores as silent context; the model is instructed not to cite raw numbers in output.
- All generated content is written in third person, referring to the business by name ("Acme Corp is currently...", "Acme Corp's approach...") — never in second person ("your business", "you are currently..."). The business name is passed to every generation call from `Client.business_name`.
- CategoryRecommendations prompts use a start/stop/continue lens as a soft generative guide — not a structural label. The model is instructed to consider what the business should start doing, stop doing, and continue doing, with the balance weighted by category performance. High-scoring categories emphasise continuation; low-scoring categories emphasise change. Every set of 7 must include all three types of guidance.
- Business Profile (company size, revenue, corporate style) is injected as qualitative context into CategorySection and CategoryRecommendations prompts only — the leaf-level generation calls. The ExecutiveSummary and RecommendationsOverview inherit this context implicitly through the content they synthesize.
