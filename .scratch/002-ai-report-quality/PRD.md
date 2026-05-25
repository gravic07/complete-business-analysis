Status: ready-for-agent

# PRD: AI Report Generation Quality — Coherence, Resilience, and Prompt Design

## Problem Statement

The current AI report generation pipeline produces each ReportSection independently using the same raw inputs (Q&A answers and numeric scores). This causes three distinct quality problems:

1. **Intra-report contradictions** — The Overall section is generated from raw answers and scores, the same inputs used for each Category section. Because the LLM derives conclusions independently for each section, the Overall section can contradict what the Category sections actually say. The report does not read as a single coherent document.

2. **Score leakage in output** — The prompt passes raw numeric scores to the LLM, and the generated content often references those numbers directly ("your score of 450 out of 1000"). Scores are an internal calculation tool, not a concept that belongs in a client-facing document.

3. **Wrong point of view** — Generated content is sometimes written about the client in third person ("the client is currently experiencing...") rather than directly to the client ("you are currently experiencing..."). The Report is delivered to the client; it should address them directly.

Additionally, the generation task is not resilient to partial failure. If the task fails after generating four of seven Category sections, the Analysis is marked failed and cannot be resumed — the advisor must resubmit feedback to trigger a new run from scratch, discarding the work already completed.

## Solution

Redesign the AI service and orchestration layer to produce a report that reads as a unified document, is written to the client, and can recover from partial failures without discarding completed work:

1. Split the AI service into two distinct generation paths: one for Category sections (focused, qualitative, no scores) and one for the Overall section (cross-cutting synthesis that reads from the assembled current Report, not from raw answers).
2. Always regenerate the Overall section after any Category section changes — not only when overall Feedback is present. The Overall reads the full assembled state of all current Category sections before generating.
3. Give the Overall section a specific mandate: execution sequencing (which category plans can run in parallel), low-hanging fruit (high-impact, easy-to-implement actions), and most urgent items — not a summary of the Category sections.
4. Remove numeric scores from Category section prompts entirely. Pass scores only to the Overall section as silent urgency context, with an explicit instruction not to cite raw numbers.
5. Make the generation task idempotent so a failed Analysis can be retried in-place by re-running the same task against the same Analysis record.

## User Stories

1. As a client receiving a Report, I want the Overall section to tell me which actions I should tackle first and which can run in parallel, so that I have a clear starting point rather than seven equal-weight category plans.
2. As a client receiving a Report, I want the Overall section to call out the easiest wins — things I can implement quickly that have a large impact — so that I can build momentum early.
3. As a client receiving a Report, I want every section to speak to me directly ("your business", "you are currently..."), so that the Report feels like it was written for me rather than about me.
4. As a client receiving a Report, I want the Overall section to be consistent with what each Category section says, so that I am not reading contradictory recommendations in the same document.
5. As a client receiving a Report, I want the Category sections to describe my situation in qualitative terms, so that the report reads as a professional assessment rather than a scorecard.
6. As an advisor reviewing a Report, I want the Overall section to synthesize the Category sections I just read, not re-analyse the same raw answers independently, so that the summary reflects what the individual sections actually concluded.
7. As an advisor reviewing a Report, I want the Overall section to always reflect the current state of all Category sections — including ones I just regenerated via targeted Feedback — so that I never see a stale summary after making a targeted change.
8. As an advisor reviewing a Report, I want the Category sections to not reference raw numeric scores in their text, so that I can deliver the Report directly to a client without editing out internal calculation details.
9. As an advisor, I want a failed Analysis to be retryable without creating a new Analysis record, so that the audit trail is not polluted with abandoned runs and the work already completed is not discarded.
10. As an advisor, I want a retry to pick up from the last successfully completed Category section, so that re-running a failed Analysis does not regenerate sections that were already produced correctly.
11. As an advisor, I want targeted Category Feedback to trigger an Overall section regeneration as well, so that the Overall always reflects the updated Category content after any feedback cycle.
12. As an advisor, I want the Overall section regeneration to see the full assembled Report — including Category sections from earlier Analysis runs that were not in scope this time — so that the synthesis is always complete regardless of which categories were touched in the latest run.

## Implementation Decisions

### AI Service: two distinct generation paths

The current single `generate_section` function is replaced by two functions with different signatures and fundamentally different prompt structures:

**`generate_category_section`** — generates a focused narrative for one business category.
- Inputs: the Q&A answers for that category, optional prior section content, optional feedback text, optional LLM client.
- No numeric scores in the prompt — severity and urgency are communicated through the qualitative content of the answers.
- No section title injected into the prompt (prevents the model from surfacing the heading in the output).
- Written to the client in second person throughout.

**`generate_overall_section`** — generates a cross-cutting synthesis section.
- Inputs: a mapping of category name → current section text (the full assembled Report), category scores (as silent urgency context only), optional prior overall content, optional overall feedback text, optional LLM client.
- The model is explicitly instructed not to cite raw scores in output — scores are provided only to inform urgency ranking.
- The prompt specifies the Overall's four-part mandate: (1) brief acknowledgment of the overall picture, (2) execution sequencing, (3) low-hanging fruit, (4) most urgent items.
- Written to the client in second person throughout.

Both functions are pure in the same way the current `generate_section` is: they receive plain data, return plain text, and accept an injectable LLM client for testing.

### Analysis Orchestrator: Overall section regeneration rule

The condition that guards Overall section generation changes from "first run or overall feedback present" to "always regenerate after all Category sections are written."

When generating the Overall section, the orchestrator fetches the latest ReportSection per Category across all Analysis runs for the Assessment — the same assembled-Report query used by the report view. This ensures the Overall always synthesizes the complete current state of the Report, including Category sections from earlier runs that were not in scope for this Analysis.

### Analysis Orchestrator: idempotency

Before generating each Category section, the orchestrator checks whether a ReportSection already exists for that `(analysis, category)` pair. If it does, the section is skipped. This makes the task safe to re-run against the same Analysis record without duplicating work.

A failed Analysis can be retried by calling the existing Celery task with the same `analysis_pk`. The task transitions the Analysis status back to `processing`, skips already-completed sections, and resumes from the first missing one. No new Analysis record is created on retry.

### Report assembly as a shared query

The assembled-Report query (latest ReportSection per Category across all Analysis runs) is currently only used in the report view. The orchestrator needs the same query to feed the Overall section generator. This logic should live in one place and be callable from both the view and the orchestrator.

### Prompt design constraints (captured in domain docs)

These are invariants that all prompts in the system must respect, not one-off implementation choices:
- Category section prompts: no numeric scores, no section title injection.
- Overall section prompt: scores as silent context only; explicit instruction not to cite raw numbers.
- All generated content: second person throughout ("your business", "you are currently..."), never third person ("the client is...").

## Testing Decisions

Good tests verify the external behaviour of a module — its inputs and outputs — not how it is implemented internally. Tests should not assert on how many times a sub-function was called or which private methods ran.

**Modules to test:**

- **AI Service (`generate_category_section`)** — Given a set of Q&A answers and optional feedback/prior content, assert that the constructed prompt does not contain any numeric score values and does not contain a "Section:" header line. Use the injectable LLM client to capture the prompt without a real API call. Prior art: existing `test_ai_service.py` which already uses a capturing stub client.

- **AI Service (`generate_overall_section`)** — Given a mapping of category names to section text and a score dict, assert: (1) the category section text appears in the constructed prompt, (2) the score values appear in the prompt (as silent context), (3) the prompt contains instruction language for the four-part mandate (sequencing, low-hanging fruit, urgency). Use the same capturing stub pattern.

- **Analysis Orchestrator: Overall always regenerates** — Integration test: create an Analysis with category-only Feedback (no overall_text). Run the orchestrator. Assert a ReportSection with `category=None` (the Overall) is created. This tests the fixed regeneration condition.

- **Analysis Orchestrator: idempotency** — Integration test: run the orchestrator for an Analysis, let it create some ReportSections, then call the task function again against the same Analysis. Assert the total number of ReportSections for that Analysis has not increased (no duplicates created).

- **Analysis Orchestrator: Overall reads assembled state** — Integration test: set up two Analysis runs where the first run produced sections for all categories and the second run only regenerates one category. Run the orchestrator for the second Analysis. Assert the Overall section for the second run was generated with content drawn from all categories (including the unchanged ones from the first run).

Testing prior art: `test_ai_service.py` demonstrates the injectable LLM client pattern. The Analysis integration tests in the existing issues use `Assessment` fixtures with real answers — follow the same fixture setup.

## Out of Scope

- Full version chain history in regeneration prompts (passing all prior versions of a section and their associated feedback to the LLM). Deferred until there is a concrete reported case of a section degrading across multiple feedback cycles.
- Parallel generation of Category sections via Celery chord. Generation runs async and advisors poll status, so wall-clock time is not a pressing concern. Can be revisited if generation time becomes a user complaint.
- A UI retry button for failed Analysis records. The retry mechanism (calling the task with the same `analysis_pk`) is the backend contract; surfacing it in the UI is a separate piece of work.
- Streaming AI responses to the UI.
- PDF export or print layout.

## Further Notes

- See [ADR-0003](../../docs/adr/0003-overall-section-generated-from-assembled-category-content.md) for the decision to generate the Overall from assembled Category section content rather than raw Q&A.
- See [ADR-0004](../../docs/adr/0004-analysis-task-idempotent-for-resilience.md) for the decision to make the task idempotent rather than using Celery chords or always creating a new Analysis on retry.
- The PHP predecessor (`llm-service.php`, `report-prompts.php`) generated the whole report as one sequential conversation with shared message history, which gave natural coherence but prevented individual section regeneration. The design in this PRD achieves coherence through the Overall section reading assembled Category content, while preserving individual section regeneration for the feedback cycle.
- `max_tokens` on the LLM client does not need to increase. Each section is generated independently; at ~1,024 tokens per section across 7 Category sections plus one Overall, the full assembled Report lands within the 2,000–3,000 word target.
