# Split ReportSection into CategorySection and ExecutiveSummary

`ReportSection` was a single model that covered two structurally different things: category-level sections (distinguished by a non-null `category` FK) and the overall section (distinguished by `category=None`). These were unified under one model because they were both AI-generated narrative blobs stored in a single `content` field.

When category sections were redesigned to have three named sub-sections — Overview, Impact, and Path Forward — the two variants diverged structurally. A `CategorySection` holds three distinct prose fields; an `ExecutiveSummary` holds one prose blob. Keeping them in one model would require three nullable fields on every `ExecutiveSummary` row and one unused `content` field on every `CategorySection` row. The `category=None` sentinel, already a workaround, would then also be encoding which fields are valid — type information spread across a nullable FK and nullable content fields.

The alternative considered was keeping one model with nullable fields and relying on the `category` nullability as a discriminator. This was rejected because the structural divergence is genuine and permanent, not incidental. Two models with no nullable fields is the honest representation.

## Consequences

- `ReportSection` is replaced by `CategorySection` (fields: `analysis`, `category`, `overview`, `impact`, `path_forward`) and `ExecutiveSummary` (fields: `analysis`, `content`)
- The `unique_together` constraint splits: `CategorySection` retains `[analysis, category]`; `ExecutiveSummary` gets `[analysis]`
- Report assembly changes from one query across a single model to two queries — one for the latest `ExecutiveSummary`, one for the latest `CategorySection` per category
- `generate_category_section()` returns a structured object (or three separate strings) instead of a single string; `generate_overall_section()` continues to return a single string
- ADR 0002 (live-assembled view) and ADR 0003 (overall section from assembled category content) remain valid — the assembly strategy and generation source are unchanged
