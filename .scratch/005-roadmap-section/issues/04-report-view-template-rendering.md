Status: complete

# Report view and template: Roadmap section rendering

## Parent

[PRD: Roadmap Section](../PRD.md)

## What to build

Extend the report view to pass the latest `Roadmap` to the template context, and add the Roadmap section to the report template. The section appears after the Recommendations section and is hidden entirely when no `Roadmap` exists for the Assessment.

The rendered Roadmap section has five parts:

1. **Overview** — a static three-paragraph template explaining what the Roadmap is and how to use it. This text is a module-level constant in Python, not fetched from the database. It is identical for every client.
2. **Monthly Plans** — 12 plan blocks, each labelled "Month N" (derived from array index, not stored). Each block shows three labelled lists: Goals, Action Items, and Challenges.
3. **Potential Challenges** — the `potential_challenges` JSON array rendered as sequential paragraphs.
4. **Post-Implementation Outcomes** — the `post_implementation_outcomes` JSON array rendered as sequential paragraphs.
5. **Closing Reflections** — the `closing_reflections` JSON array rendered as sequential paragraphs.

The view passes `roadmap` as a single context variable (the `Roadmap` instance or `None`). The template guards the entire section on `{% if roadmap %}`.

## Acceptance criteria

- [x] Report view passes `roadmap` (result of `latest_roadmap(assessment)`) to the template context
- [x] Roadmap section is rendered after the Recommendations section when a `Roadmap` exists
- [x] Roadmap section is not rendered (no empty placeholder) when no `Roadmap` exists
- [x] Static Overview renders as three paragraphs; the text is a constant in code, not stored in the database
- [x] Monthly Plans render 12 blocks labelled "Month 1" through "Month 12" in order
- [x] Each monthly block shows three labelled lists — Goals, Action Items, Challenges — each with 5 items
- [x] Potential Challenges, Post-Implementation Outcomes, and Closing Reflections each render as sequential paragraphs from their respective JSON arrays
- [x] All Roadmap content is written in third person (enforced at generation time, but confirmed visible in the rendered output)

## Blocked by

- [03 — Pipeline integration: Roadmap generation step](./03-pipeline-integration.md)
