Status: ready-for-agent

# PDF service module and Celery task

## What to build

Two things that wire the PDF template into the async generation pipeline.

**Signed-token authentication** — replace the localhost bypass from issue 04 with a short-lived signed token (using Django's `TimestampSigner`) passed as a query parameter to the PDF template view. The `generate_pdf_export` Celery task generates and passes the token; the view validates it. This keeps the PDF URL protected even from other local processes while still being accessible to Playwright running on the same server.

**`pdf_service.py`** — a module in the `reports` app that encapsulates all Playwright logic. Public interface: `generate_pdf(assessment_pk, token) -> bytes`. Internally:
- Launches a Playwright Chromium browser (sync API)
- Navigates to the PDF template URL with the signed token as a query param
- Waits for ApexCharts SVGs to finish rendering (wait for SVG elements to appear in the DOM)
- Calls `page.pdf()` with US Letter size (`width: 8.5in, height: 11in`), print media type, and Playwright's `headerTemplate`/`footerTemplate` HTML strings for the dark navy header and footer
- Returns the PDF bytes
- Raises a descriptive exception on failure

Header template (dark navy bar, white text): Assessment name (uppercased) left-aligned, client business name right-aligned.
Footer template (dark navy bar, white text): `<span class="pageNumber">` left-aligned, "COMPLETE BUSINESS REPORT" right-aligned.
Cover page has zero top margin (`@page :first`) so the header/footer are not injected on page 1.

**`generate_pdf_export` Celery task** — in the `reports` app tasks file. Accepts `pdf_export_id: str`. Flow:
1. Fetch `PDFExport` by ID; if already `complete` or `failed`, return early (idempotency guard)
2. Transition status to `processing`
3. Generate signed token; call `pdf_service.generate_pdf()`
4. Save the returned bytes to `PDFExport.file` as `<assessment_pk>_<pdf_export_pk>.pdf`
5. Transition status to `complete`
6. On any exception: transition status to `failed`, re-raise

Add `playwright` (Python package) and `chromium` browser binary to project dependencies and deployment configuration.

## Acceptance criteria

- [ ] `playwright` is in the project dependencies and `chromium` binary is installed
- [ ] PDF template view rejects requests without a valid signed token (returns 403)
- [ ] PDF template view accepts requests with a valid signed token
- [ ] `pdf_service.generate_pdf()` returns bytes that constitute a valid PDF (starts with `%PDF`)
- [ ] The generated PDF is US Letter size
- [ ] A `PDFExport` that completes successfully has status `complete` and a non-null `file`
- [ ] A `PDFExport` whose generation raises an exception has status `failed` and a null `file`
- [ ] An already-`complete` `PDFExport` passed to the task returns early without re-generating
- [ ] Status transition tests use Django `TestCase` and mock `pdf_service.generate_pdf`

## Blocked by

- `04-pdf-template-and-view.md` — needs the PDF template URL to exist
