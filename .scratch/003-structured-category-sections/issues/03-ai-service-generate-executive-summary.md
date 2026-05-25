Status: ready-for-agent

# AI service: generate_executive_summary

## Parent

PRD: `.scratch/003-structured-category-sections/PRD.md`

## What to build

Rename `generate_overall_section` to `generate_executive_summary` and replace its prompt mandate. The function signature stays the same shape (assembled category sections dict, scores dict, max scores dict, optional prior content, optional feedback text, injectable client), but the prompt changes from a four-part sequencing/urgency mandate to a pure synthesis mandate.

The new prompt instructs the LLM to weave the category sections into a coherent holistic picture of the business in 4-5 paragraphs. It does not ask for execution sequencing, low-hanging fruit identification, or urgency ranking — those are now handled within each `CategorySection`'s Path Forward sub-section. The prompt continues to pass scores as silent context only and explicitly instructs the model not to cite raw numbers in output. All content is written to the client in second person.

Update all existing tests for `generate_overall_section` to use the new function name and updated mandate. Remove the test that asserts the prompt contains sequencing/urgency language. Add a test asserting the prompt does not contain that language. Add a test asserting the prompt instructs a 4-5 paragraph synthesis.

## Acceptance criteria

- [ ] `generate_executive_summary` function exists and `generate_overall_section` is removed
- [ ] The prompt instructs 4-5 paragraphs of synthesis, not sequencing or urgency ranking
- [ ] The prompt does not contain "sequencing", "simultaneously", "low-hanging fruit", or "urgent" language
- [ ] The prompt passes scores as silent context with an explicit instruction not to cite raw numbers in output
- [ ] The prompt instructs second person throughout
- [ ] When prior content is provided, it appears in the prompt
- [ ] When feedback text is provided, it appears in the prompt
- [ ] All category section texts passed via `category_sections` appear in the prompt
- [ ] All tests for `generate_executive_summary` pass

## Blocked by

None — can start immediately.
