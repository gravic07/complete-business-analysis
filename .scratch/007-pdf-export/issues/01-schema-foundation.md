Status: complete

# Schema foundation: Assessment.name and PDFExport model

## What to build

Add two schema changes that the rest of the PDF export feature depends on.

**`Assessment.name`** — a short `CharField` (max 100 chars) on the existing `Assessment` model. Defaults to `"Initial Report"`. This field appears on the PDF cover page (as typed) and in the PDF page header (uppercased). It is editable by the advisor at any time from the Report page.

**`PDFExport` model** — a new model in the `reports` app that tracks one async PDF generation job. Fields:
- `assessment` — FK to `Assessment`, cascade delete
- `status` — CharField with choices: `pending`, `processing`, `complete`, `failed`
- `file` — FileField, nullable; populated when status reaches `complete`
- UUID primary key and timestamps inherited from `BaseModel`

One Assessment can have many `PDFExport` records. The UI will always poll the most recently created one.

Include migrations for both changes.

## Acceptance criteria

- [x] `Assessment.name` field exists with default `"Initial Report"` and max_length 100
- [x] `PDFExport` model exists in the `reports` app with `assessment` FK, `status` choices, and nullable `file` FileField
- [x] Both changes have migrations that apply cleanly
- [x] Unit test asserts `Assessment.name` defaults to `"Initial Report"` on a new instance
- [x] Unit test asserts `PDFExport.status` choices are exactly `pending`, `processing`, `complete`, `failed`
- [x] `PDFExport` is registered in the Django admin

## Blocked by

None — can start immediately.
