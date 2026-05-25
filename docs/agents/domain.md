# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — single global glossary covering all layers (Django models, analysis pipeline, report assembly, feedback cycle)
- **`docs/adr/`** — read ADRs that touch the area you're about to work in

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront.

## File structure

This is a single-context repo:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-analysis-stored-as-intermediate-record.md
│       └── 0002-report-as-live-assembled-view.md
└── complete_business_analysis_tool/
```

There is no `CONTEXT-MAP.md`. Do not look for per-app or per-directory `CONTEXT.md` files — the root one covers the full domain.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Key terms: Assessment, Analysis, CategoryScore, Report, ReportSection, Feedback, CategoryFeedback, Score, Plan.

Don't drift to synonyms. For example: use **ReportSection**, not "report chunk" or "plan section"; use **Feedback**, not "comment" or "review".

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/grill-with-docs`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0002 (report as live assembled view) — but worth reopening because…_
