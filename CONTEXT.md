# Domain Context

## Glossary

### Assessment
A completed set of answers submitted by an advisor on behalf of a Client, based on an AssessmentTemplate. An Assessment is the starting point for all analysis. It is immutable once submitted — answers are preserved via snapshots.

### Analysis
A single run of the scoring and AI-generation process against an Assessment. Stored as a persistent record. Inputs include: computed scores (total + per-category), question/answer content, and any Feedback from a prior Report. Produces exactly one Report. An Assessment can have many Analysis runs over its lifetime.

### Report
A live view assembled at render time from the latest ReportSection per Category across all Analysis runs for an Assessment. Not stored as a monolithic document — it is always the most current section per category. Advisors submit Feedback against the Report, which triggers a new Analysis run covering only the categories that received feedback.

**Report audience:** The Report is written directly to the Client in second person ("you", "your business") — not about the Client in third person ("the client is currently..."). Advisors review the Report for accuracy before delivering it to the Client and assisting with implementation, but the Client is the intended reader of the final document.

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
The AI-generated content inside a Report — actionable recommendations derived from the content of questions and answers, not just their scores. Advisors can influence a Plan by submitting Feedback, which produces a new Report. A Plan consists of two distinct layers:

- **Category Section** — a focused analysis of one business area structured as three named sub-sections: Overview (current state summary), Impact (how the current state affects the business), and Path Forward (short description of changes needed). Generated from that category's Q&A answers only.
- **Executive Summary** — a true synthesis of the full report, condensing and stitching together the Category Sections into a coherent holistic picture. Does not carry a sequencing or urgency mandate — those are handled within each Category Section's Path Forward. Generated from the full text of all Category Sections — not from raw Q&A data. Rendered as 4-5 paragraphs with no Overview/Impact/Path Forward structure.

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
- `Analysis` produces many `CategoryScore` records, many `CategorySection` records, and one `ExecutiveSummary`
- `CategorySection` belongs to one `Analysis` and one `Category`
- `ExecutiveSummary` belongs to one `Analysis`
- `Feedback` belongs to one `Assessment`, has optional `overall_text` and many `CategoryFeedback` records
- `CategoryFeedback` belongs to one `Feedback` and one `Category`

## Model Layout

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
- All generated content is written directly to the Client in second person ("your business", "you are currently...") — never in third person ("the client is..."). Advisors review Reports before delivery but the Client is the intended reader.
