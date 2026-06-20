Status: ready-for-agent

# Assessment name inline edit on the Report page

## What to build

An editable field for `Assessment.name` on the Report page, positioned near the top of the page where the Download PDF button will appear (issue 07). The advisor can rename the assessment at any time without navigating away.

The field displays the current `Assessment.name` value on load. On submission it POSTs to a dedicated update endpoint, saves the new name to `Assessment.name`, and reflects the updated value on the page. The interaction should be lightweight — a small inline form or HTMX partial that does not reload the full report.

The field should be clearly labelled (e.g. "Report Name") so the advisor understands it controls the PDF cover page and header.

## Acceptance criteria

- [ ] `Assessment.name` is visible and editable at the top of the Report page
- [ ] The field pre-populates with the current `Assessment.name` value
- [ ] Submitting a new name saves it to `Assessment.name` in the database
- [ ] The updated name is reflected on the page without a full page reload
- [ ] An empty submission is rejected (name is required)
- [ ] The field is only visible when the Report page has content (same condition as the rest of the report)
- [ ] Django `TestCase` asserts the update endpoint saves the name and returns a success response
- [ ] Django `TestCase` asserts the update endpoint rejects an empty name

## Blocked by

- `01-schema-foundation.md` — needs `Assessment.name` field
