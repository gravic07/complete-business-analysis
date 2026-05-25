Status: done

# AI Service — category section generation

## Parent

[PRD: AI Report Generation Quality](./../PRD.md)

## What to build

Add a `generate_category_section` function to the AI service that replaces `generate_section` for category-level ReportSection generation. The new function has a narrower signature: it accepts Q&A answers for one category, optional prior section content, and optional feedback text. It does not accept scores.

The prompt must satisfy three constraints:
- No numeric scores anywhere in the prompt — severity and urgency are communicated entirely through the qualitative content of the answers.
- No section title injected into the prompt — the current "Section: {scope_label}" line is removed to prevent the model surfacing the heading in the output.
- All generated content written to the client in second person ("your business", "you are currently...") — never third person ("the client is...").

The old `generate_section` function stays in place until the orchestrator is updated in issue 03. The new function should coexist alongside it.

## Acceptance criteria

- [x] `generate_category_section` exists in the AI service module and accepts: answers (list of Q&A dicts), optional prior_content, optional feedback_text, optional llm_client
- [x] The prompt constructed by `generate_category_section` contains no numeric score values
- [x] The prompt constructed by `generate_category_section` contains no "Section:" header line
- [x] The prompt instructs the model to write in second person, addressing the client directly
- [x] Unit tests use the injectable stub LLM client (same pattern as existing `test_ai_service.py`) to capture and assert on the prompt without making real API calls
- [x] Tests pass for the no-scores constraint, no-header constraint, and second-person instruction

## Blocked by

None — can start immediately.
