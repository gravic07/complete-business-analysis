Status: ready-for-agent

# Start Assessment: create a draft Assessment from client + template selection

## What to build

A new, slimmed-down entry point that creates the `Assessment` record immediately upon client+template selection, rather than only at the end of a fully-answered form.

**`AssessmentStartForm`** — a small form with just a `client` field (template comes from the URL, as today's `AssessmentEntryForm` already does). On save, creates an `Assessment` with `template`, `client`, and default `status="draft"`. No answers, no guidance — those are separate steps.

**`AssessmentStartView`** — `FormView` using `AssessmentStartForm`, replacing the client-selection responsibility of today's `AssessmentEntryView`. Accepts a `?client=` query param to pre-fill the client field, matching today's behavior (used by the client detail page's "Start an assessment…" control). On success, redirects to the Assessment detail page (`assessments:detail`) for the newly created Assessment — this becomes the hub page in a later slice; for now it will render using the existing (unmodified) detail template.

**Routing** — new URL for `AssessmentStartView`, scoped under the template pk (e.g. `assessments/<template_pk>/start/`). Update the template-list page and the client-detail page's "Start an assessment…" link to point here instead of the old `assessments:entry` URL.

Leave `AssessmentEntryView`/`AssessmentEntryForm` and their URL in place for now — they still work end-to-end for answering questions and are only retired once the Answer step slice replaces their question-answering responsibility.

## Acceptance criteria

- [ ] `AssessmentStartForm` has only a `client` field, scoped to a template passed in at construction time
- [ ] Submitting the form creates an `Assessment` with the chosen client, the template from the URL, and `status="draft"`
- [ ] No `Answer` or `CategoryGuidance` records are created by this flow
- [ ] `?client=<pk>` pre-fills the client field, matching today's `AssessmentEntryView` behavior
- [ ] Successful submission redirects to `assessments:detail` for the new Assessment
- [ ] Template-list page's template links point to the new start URL
- [ ] Client-detail page's "Start an assessment…" control points to the new start URL (with `?client=` prefilled)
- [ ] View requires login (`LoginRequiredMixin`), matching existing views
- [ ] Test asserts a valid POST creates a draft Assessment and redirects correctly
- [ ] Test asserts an invalid POST (no client selected) re-renders the form with errors, no Assessment created

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs `Assessment.status` to exist
