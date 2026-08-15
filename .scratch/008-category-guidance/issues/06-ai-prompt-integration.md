Status: ready-for-agent

# AI prompt integration: CategoryGuidance flows into every Analysis run

## What to build

Wire `CategoryGuidance` text into category-section generation, labeled distinctly from advisor `Feedback` so the model doesn't conflate "focus on this area" (forward-looking, supplied before any Report exists) with "revise this" (corrective, supplied after reviewing generated content).

**`reports/ai_service.py::_build_category_prompt()`** — add a `guidance_text` parameter, appended as its own labeled line, separate from the existing `feedback_text` line. Follow the existing pattern at the `feedback_text` injection site (append a blank line + a labeled line, only when non-empty):
```python
if guidance_text:
    lines.append("")
    lines.append(f"Advisor guidance provided before the assessment: {guidance_text}")
```
placed independently of the `feedback_text` block so both can appear together, either alone, or neither.

**`analysis/tasks.py`** — fetch the assessment's `CategoryGuidance` per category (`assessment.category_guidance.all()`, keyed by `category_id`) and pass the matching category's text through to `generate_category_section()` as `guidance_text`, on every Analysis run for the assessment — the initial run and every later re-analysis — independent of whatever `combined_feedback` resolves to for that run. This mirrors how `category_feedback_by_id` is already built and looked up today, but guidance is looked up unconditionally on every run rather than only when a `Feedback` record is present.

## Acceptance criteria

- [ ] `_build_category_prompt()` accepts `guidance_text` and appends it as a line labeled distinctly from `feedback_text` (different label text)
- [ ] When both `guidance_text` and `feedback_text` are present, both lines appear in the prompt, clearly separated
- [ ] When only one is present, only that one's line appears
- [ ] When neither is present, neither line appears (no regression to existing feedback-only behavior)
- [ ] `analysis/tasks.py` passes each category's `CategoryGuidance.text` through on the assessment's first Analysis run
- [ ] `analysis/tasks.py` passes each category's `CategoryGuidance.text` through on a second (re-)analysis run for the same assessment, regardless of whether that run also has `Feedback`
- [ ] A category with no `CategoryGuidance` row passes `guidance_text=None` (or empty), not an error
- [ ] Tests exercise `_build_category_prompt()` directly for the labeling assertions, and `analysis/tasks.py`'s category-lookup logic for the run-independence assertions, following existing prompt-building test patterns in the `reports`/`analysis` apps

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs the `CategoryGuidance` model
