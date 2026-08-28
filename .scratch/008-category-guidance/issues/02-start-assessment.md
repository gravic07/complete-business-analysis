Status: complete

# Start Assessment: create a draft Assessment from client + template selection

## What to build

A new, slimmed-down entry point that creates the `Assessment` record immediately upon client+template selection, rather than only at the end of a fully-answered form.

**`AssessmentStartForm`** — a small form with just a `client` field (template comes from the URL, as today's `AssessmentEntryForm` already does). On save, creates an `Assessment` with `template`, `client`, and default `status="draft"`. No answers, no guidance — those are separate steps.

**`AssessmentStartView`** — `FormView` using `AssessmentStartForm`, replacing the client-selection responsibility of today's `AssessmentEntryView`. Accepts a `?client=` query param to pre-fill the client field, matching today's behavior (used by the client detail page's "Start an assessment…" control). On success, redirects to the Assessment detail page (`assessments:detail`) for the newly created Assessment — this becomes the hub page in a later slice; for now it will render using the existing (unmodified) detail template.

**Routing** — new URL for `AssessmentStartView`, scoped under the template pk (e.g. `assessments/<template_pk>/start/`). Update the template-list page and the client-detail page's "Start an assessment…" link to point here instead of the old `assessments:entry` URL.

Leave `AssessmentEntryView`/`AssessmentEntryForm` and their URL in place for now — they still work end-to-end for answering questions and are only retired once the Answer step slice replaces their question-answering responsibility.

## Acceptance criteria

- [x] `AssessmentStartForm` has only a `client` field, scoped to a template passed in at construction time
- [x] Submitting the form creates an `Assessment` with the chosen client, the template from the URL, and `status="draft"`
- [x] No `Answer` or `CategoryGuidance` records are created by this flow
- [x] `?client=<pk>` pre-fills the client field, matching today's `AssessmentEntryView` behavior
- [x] Successful submission redirects to `assessments:detail` for the new Assessment
- [x] Template-list page's template links point to the new start URL
- [x] Client-detail page's "Start an assessment…" control points to the new start URL (with `?client=` prefilled)
- [x] View requires login (`LoginRequiredMixin`), matching existing views
- [x] Test asserts a valid POST creates a draft Assessment and redirects correctly
- [x] Test asserts an invalid POST (no client selected) re-renders the form with errors, no Assessment created

## Blocked by

- `01-assessment-lifecycle-schema-and-readiness-checker.md` — needs `Assessment.status` to exist

## Comments

Implemented as specified: `AssessmentStartForm`/`AssessmentStartView` added in `assessments/forms.py` and `assessments/views.py`, new `assessments:start` URL at `<uuid:pk>/start/`, new `assessment-start.html` template, template-list and client-detail links repointed. 9 tests added covering valid/invalid submission and `?client=` pre-fill; full suite and lint green.

As called out in the spec, this leaves a known temporary gap: assessments created via the new Start flow land on the (unmodified) detail page with no in-UI path to actually answer questions, since `assessment-list.html`/`client-detail.html` no longer link to `assessments:entry` and the detail page doesn't yet link anywhere either. This is expected to be resolved by the Answer step slice, which should either add a "continue" link from the detail/hub page or otherwise let `AssessmentEntryView` resume an existing draft `Assessment` rather than always creating a new one.
