# Roadmap generated as a single LLM tool call

The Roadmap is a 12-month synthesis artifact — the final layer of a Plan, generated after all CategoryRecommendations are complete. We generate it as a single LLM tool call (structured via tool_choice, analogous to `record_category_section`) rather than decomposing it into per-month or per-section calls as ADR-0006 did for recommendations.

The Roadmap requires arc coherence: month 1 must be sequenced with awareness of month 12. Per-month generation would require each call to re-establish the full context and could not guarantee coherent month-to-month progression across the 12-month span. This is the key difference from CategoryRecommendations, which are independent per-category artifacts.

The Roadmap also has no feedback path of its own — it only regenerates as a downstream consequence of upstream category or report-level Feedback. This makes partial regeneration (the main benefit of decomposed calls in ADR-0006) unnecessary: the entire Roadmap always regenerates together whenever upstream recommendations change.

## Consequences

The single call requires `max_tokens=8192`, the only exception to the standard 4096 token ceiling used for all other generation calls. The Roadmap generation function gets its own dedicated LLM client rather than using the shared `_default_llm_client()`.
