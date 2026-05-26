Status: complete

# AI service: generate_category_section returns structured dict

## Parent

PRD: `.scratch/003-structured-category-sections/PRD.md`

## What to build

Change `generate_category_section` in the AI service to return a dict with three keys — `overview`, `impact`, and `path_forward` — instead of a plain string. The function instructs the LLM to return valid JSON matching that shape and parses the response before returning.

The prompt must instruct the LLM to produce three named sub-sections: Overview (current state of this business area, 5-8 sentences), Impact (how the current state affects the business, 5-8 sentences), and Path Forward (changes needed to improve, 5-8 sentences). All content is written to the client in second person. No numeric scores appear in the prompt.

The `prior_content` parameter is replaced by three separate optional parameters: `prior_overview`, `prior_impact`, and `prior_path_forward`. When present, each is included in the prompt as the prior version of that sub-section for the LLM to revise.

The injectable `llm_client` parameter continues to receive a prompt string; it must now return a string that is valid JSON with the three expected keys. Tests stub this with a function returning a hardcoded JSON string such as `'{"overview": "...", "impact": "...", "path_forward": "..."}'`.

Update all existing tests for `generate_category_section` to match the new signature and return type. Add new tests asserting the returned value is a dict with all three keys as non-empty strings.

## Acceptance criteria

- [x] `generate_category_section` returns a `dict` with keys `overview`, `impact`, and `path_forward`, each a non-empty string
- [x] The prompt instructs the LLM to return JSON with those three keys
- [x] The prompt specifies 5-8 sentences per sub-section
- [x] The prompt instructs second person throughout
- [x] No numeric score values appear in the prompt (existing test must still pass)
- [x] `prior_content` parameter is replaced by `prior_overview`, `prior_impact`, and `prior_path_forward` (all optional)
- [x] When prior sub-section strings are provided, they appear in the prompt
- [x] When `feedback_text` is provided, it appears in the prompt
- [x] All tests for `generate_category_section` pass

## Blocked by

None — can start immediately.
