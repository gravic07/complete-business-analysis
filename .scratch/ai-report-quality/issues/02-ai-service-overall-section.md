Status: ready-for-agent

# AI Service — overall section generation

## Parent

[PRD: AI Report Generation Quality](./../PRD.md)

## What to build

Add a `generate_overall_section` function to the AI service for generating the Overall ReportSection. This function has a fundamentally different signature and prompt from `generate_category_section`: it does not receive raw Q&A answers. Instead it receives the fully assembled current Report as its primary input — a mapping of category name to current section text — and uses that to synthesize across all categories.

Category scores are passed as a secondary input for urgency ranking only. The prompt must explicitly instruct the model not to cite raw scores in the output.

The prompt must specify the Overall section's four-part mandate:
1. Brief acknowledgment of the overall picture
2. Execution sequencing — which category plans can be tackled simultaneously, which depend on others
3. Low-hanging fruit — high-impact actions that are easy to implement
4. Most urgent items to address first

Like `generate_category_section`, the output must be written in second person addressing the client directly.

## Acceptance criteria

- [ ] `generate_overall_section` exists in the AI service module and accepts: category_sections (dict mapping category name to section text), category_scores (dict mapping category name to score), optional prior_content, optional feedback_text, optional llm_client
- [ ] The prompt includes the full text of each category section passed in
- [ ] The prompt includes the category scores (as internal context)
- [ ] The prompt explicitly instructs the model not to cite raw numeric scores in the output
- [ ] The prompt specifies all four parts of the Overall mandate: execution sequencing, low-hanging fruit, most urgent items, and an overall acknowledgment
- [ ] The prompt instructs the model to write in second person, addressing the client directly
- [ ] Unit tests use the injectable stub LLM client to capture and assert on the prompt
- [ ] Tests verify: category section text present in prompt, scores present in prompt as context, mandate language present, no instruction to cite raw scores

## Blocked by

None — can start immediately (parallel with issue 01).
