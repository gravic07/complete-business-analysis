## Parent

[PRD: Roadmap Prose Fields — Array to TextField Migration](../PRD.md)

## What to build

Status: complete

Update the report template to render `potential_challenges`, `post_implementation_outcomes`, and `closing_reflections` as paragraph-formatted HTML instead of iterating over array items.

Replace the three `{% for item in roadmap.X %}<p>{{ item }}</p>{% endfor %}` loops in `report-detail.html` with `{{ roadmap.X|linebreaks }}` — Django's `linebreaks` filter converts `\n\n`-separated text into `<p>` tags natively.

Update `test_report_view.py` assertions to match the new rendered output — checking for `<p>`-wrapped prose content rather than individual array item strings.

## Acceptance criteria

- [x] The Potential Challenges, Post-Implementation Outcomes, and Closing Reflections sections in `report-detail.html` use `|linebreaks` instead of a `{% for %}` loop
- [x] The rendered report HTML wraps each paragraph in `<p>` tags for all three sections
- [x] `test_report_view.py` mock values for these three fields are updated to strings; assertions verify `<p>`-tagged paragraph content in the rendered response
- [x] All existing report view tests pass

## Blocked by

- [01 — Migrate Roadmap prose fields from JSONField to TextField](01-migrate-roadmap-prose-fields.md)
