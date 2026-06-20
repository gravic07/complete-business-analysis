Status: ready-for-agent

# PDF Export for Finished Reports

## Problem Statement

Advisors currently have no way to produce a shareable, print-ready document from a finished Report. Once an Assessment has been analyzed and the Report reviewed, advisors need to deliver the findings to their clients. Without a PDF export, they must either print the web page directly (poor formatting, navigation chrome included, interactive charts don't print cleanly) or manually recreate the report content elsewhere. This creates extra effort before every client delivery and risks presenting an unprofessional output.

## Solution

Add a "Download PDF" button to the Report page that generates a professionally formatted, multi-section PDF matching the style of the existing example report. The PDF is generated asynchronously in the background using a headless browser (Playwright), so the advisor is not blocked while it renders. The UI polls until the job completes and then triggers the download automatically.

The PDF covers all major Report sections in a logical reading order — cover page, table of contents, score overview, visualizations, analysis, recommendations, and roadmap — with consistent headers, footers, and page numbers throughout.

## User Stories

1. As an advisor, I want a "Download PDF" button at the top of the Report page, so that I can initiate a PDF export without having to scroll through the entire report first.
2. As an advisor, I want the PDF export button to be available as soon as the first Analysis is complete, so that I can export at any stage of the feedback cycle.
3. As an advisor, I want the PDF to be generated in the background while I continue working, so that I am not blocked waiting for the render to complete.
4. As an advisor, I want the page to show a progress indicator while the PDF is generating, so that I know the export is in progress.
5. As an advisor, I want the PDF to download automatically when it is ready, so that I don't have to take any extra steps after clicking the button.
6. As an advisor, I want to give each Assessment a meaningful name (e.g. "Initial Report", "Q2 Review"), so that the PDF cover page and header clearly identify which version of the report this is.
7. As an advisor, I want the Assessment name to default to "Initial Report", so that common reports require no extra configuration.
8. As an advisor, I want to edit the Assessment name directly on the Report page at any time, so that I can rename it before generating a PDF without navigating away.
9. As an advisor, I want the PDF cover page to display the Peak Performance Partners logo, a professional cover image, the report title, the client's business name, the Assessment name, and the date prepared, so that the document is immediately identifiable and professional in appearance.
10. As an advisor, I want every page after the cover page to display a header with the Assessment name (uppercased) on the left and the client's business name on the right, so that each printed page is clearly identified.
11. As an advisor, I want every page after the cover page to display a footer with the page number on the left and "COMPLETE BUSINESS REPORT" on the right, so that printed pages can be navigated and reordered easily.
12. As an advisor, I want the PDF to include a table of contents with section names and page numbers, so that the client can navigate the printed document without reading every page.
13. As an advisor, I want the PDF to include a Score Overview page showing the overall CBA Score, a categories visualization, and the per-category scores, so that the client gets an immediate quantitative summary.
14. As an advisor, I want the PDF to include a Visualizations page with the bar chart (Category Scores) and radar chart (Holistic Business Visualization) rendered from the live ApexCharts, so that the charts in the PDF match what the advisor sees on the Report page.
15. As an advisor, I want all Analysis sections to appear together in the PDF (Executive Summary first, then one page per category), so that the analysis is easy to read as a continuous narrative.
16. As an advisor, I want all Recommendations sections to appear together in the PDF (Overview first, then one page per category), so that the recommendations are grouped and easy to action.
17. As an advisor, I want the Roadmap section to include the overview, all 12 monthly plans, and the Potential Challenges, Post-Implementation Outcomes, and Closing Reflections, so that the full implementation plan is included in the PDF.
18. As an advisor, I want the PDF to not include a Conclusion section, so that the document is not redundant with the Executive Summary.
19. As an advisor, I want the PDF to be US Letter size, so that it prints correctly on standard North American paper.
20. As an advisor, I want to be able to re-download the most recently generated PDF without triggering a new generation, so that I don't have to wait again if I need a second copy.
21. As an advisor, I want to see a clear error message if PDF generation fails, so that I know to try again.
22. As an advisor, I want the static assets used on the cover page and score overview (logo, cover background image, categories chart image) to be served reliably from the application's static file storage, so that they are always available during PDF generation.

## Implementation Decisions

### Schema Changes

**`Assessment.name` field** — A short `CharField` (max ~100 chars) added to the existing `Assessment` model. Defaults to `"Initial Report"`. Appears on the PDF cover page as typed and in the PDF page header uppercased.

**`PDFExport` model** — New model in the `reports` app. Fields:
- `assessment` — FK to `Assessment`, cascade delete
- `status` — CharField with choices: `pending`, `processing`, `complete`, `failed`
- `file` — FileField (nullable; populated when status reaches `complete`)
- Inherits `id` (UUID) and timestamps from `BaseModel`

One Assessment can have many PDFExport records. The UI polls the most recent one.

### Modules

**ToC page number calculator** — A pure function module that accepts the report's structural parameters (number of categories) and returns a mapping of section name → page number. Most sections are exactly one page. The fixed page structure is:

```
1  — Cover Page (no header/footer)
2  — Table of Contents
3  — Score Overview
4  — Visualizations
5  — Analysis: Executive Summary
6  to 6+N-1  — Analysis: one page per category (N categories)
6+N  — Recommendations: Overview
6+N+1 to 6+2N  — Recommendations: one page per category
6+2N+1  — Roadmap: Overview
6+2N+2 to 6+2N+13  — Roadmap: Month 1–12
6+2N+14  — Potential Challenges
6+2N+15  — Post-Implementation Outcomes
6+2N+16  — Closing Reflections
```

This is a pure function with no DB access — directly testable with unit tests.

**PDF service module** — Encapsulates all Playwright logic. Public interface: `generate_pdf(assessment_pk: UUID) -> bytes`. Internally: launches a Playwright browser, authenticates or bypasses auth to access the PDF template URL, waits for ApexCharts SVGs to finish rendering, calls `page.pdf()` with US Letter size and header/footer templates, returns the PDF bytes. No Django model access — accepts a PK, handles the rest.

**PDF Celery task** — `generate_pdf_export(pdf_export_id: str)`. Fetches the `PDFExport` record, transitions status to `processing`, calls the PDF service, saves the resulting bytes to `PDFExport.file`, transitions to `complete`. On any exception, transitions to `failed`. Follows the same idempotency and status-transition pattern as `run_analysis`.

**PDF template view** — A Django view that assembles the full PDF context (same data as `ReportView` plus the ToC page map) and renders the dedicated PDF template. This is the URL Playwright navigates to. It must be accessible during Playwright's headless request — authentication should either be bypassed for localhost requests or handled via a short-lived token passed as a query parameter.

**Export trigger endpoint** — A POST view on the Report page that creates a `PDFExport` record with status `pending`, queues the Celery task, and returns the `PDFExport` UUID as JSON. The front end uses this UUID to poll for status.

**Polling endpoint** — A GET view that accepts a `PDFExport` UUID and returns JSON: `{status, download_url}`. When status is `complete`, `download_url` is the file URL for the browser to follow. The front end polls this endpoint on a short interval and stops when status is `complete` or `failed`.

**Assessment name inline edit** — A small form (or HTMX partial) on the Report page that saves `Assessment.name` on submission. Shown as an editable field near the top of the page, adjacent to the Download PDF button.

### PDF Template Structure

The dedicated PDF template (`report-pdf.html`) renders a single HTML page with all sections in sequence. Page breaks are enforced with `page-break-before: always` CSS on each section. The cover page uses `@page :first { margin: 0; }` to suppress header/footer only on the first page.

Sections in order:
1. Cover Page — logo, cover image, report title, client name, Assessment name, date
2. Table of Contents — section names with calculated page numbers
3. Score Overview — intro text, CBA Score, categories-pie-chart.png (static), per-category score list
4. Visualizations — ApexCharts bar chart and radar chart (same chart config as web report)
5. Analysis: Executive Summary
6. Analysis: one section per category (Overview, Impact, Path Forward)
7. Recommendations: Overview
8. Recommendations: one section per category (numbered list of 7)
9. Roadmap: Overview (static boilerplate)
10. Roadmap: Month 1–12 (Goals, Action Items, Challenges per month)
11. Potential Challenges
12. Post-Implementation Outcomes
13. Closing Reflections

ApexCharts in the PDF template uses the same inline JSON injection pattern as the web report (`chart_data|safe`). Playwright waits for the SVGs to appear in the DOM before calling `page.pdf()`.

### Static Asset Locations

`cover-bg-img.jpg` and `categories-pie-chart.png` are moved from the repo root to `static/images/` alongside `company-logo.png`. No other changes to these files.

### Playwright Authentication

Playwright runs on the same server as Django. The PDF template view should be accessible to requests originating from localhost without full session auth, or the `PDFExport` task should pass a short-lived signed token as a query param that the view validates. A signed token is preferred — it keeps the view protected even from other local processes.

### PDF Header/Footer

Playwright's `headerTemplate` and `footerTemplate` HTML strings inject per-page metadata. The header contains the Assessment name uppercased on the left and the client business name on the right, styled as a dark navy bar. The footer contains `<span class="pageNumber">` on the left and "COMPLETE BUSINESS REPORT" on the right. Both are excluded from page 1 (the cover) via `margin-top: 0` on `:first` page.

## Testing Decisions

Good tests verify observable behavior at a stable interface boundary, not internal implementation. They should not import private helpers or assert on query counts.

**ToC page number calculator** — Unit tests. Pure function with no side effects. Test that given N categories, each section receives the correct page number. Test boundary values (minimum 1 category). This module is the highest-value test target because it is pure logic and failures will silently produce wrong page numbers in every PDF.

**`PDFExport` model status transitions** — Django `TestCase`. Assert that a task moving a `PDFExport` from `pending → processing → complete` ends with a file attached and correct status. Assert that a failure path lands on `failed` with no file. Prior art: look at how `Analysis` status is tested in the `analysis` app tests.

**Export trigger endpoint** — Django `TestCase` with a test client. POST to the trigger URL, assert a `PDFExport` record is created with `pending` status and the Celery task is queued (mock `generate_pdf_export.delay`). Assert the response JSON contains the PDFExport UUID.

**Polling endpoint** — Django `TestCase`. Assert that for a `complete` PDFExport, the response includes `download_url`. Assert that for a `failed` record, the response status field is `failed`.

**PDF service module** — Integration test only. Requires a running Django dev server and Playwright installed. Not suitable for the standard unit test suite; should be gated behind an environment variable or run separately.

**Assessment name field** — Django `TestCase`. Assert the default value is `"Initial Report"`. Assert saving a custom name persists correctly.

## Out of Scope

- Dynamic generation of the categories pie/wheel chart on the Score Overview page (static image used for now; planned for a future update)
- LLM-generated Roadmap Overview (static boilerplate used for now; planned for a future update)
- Two-pass ToC page number generation (single-pass calculated approach used; upgrade path exists if inaccuracies are frequent in practice)
- International (A4) page size support
- PDF version history or comparison between export runs
- Emailing the PDF directly to the client from within the application
- Any changes to the web report template (`report-detail.html`)

## Further Notes

- ADR-0008 documents the decision to use ApexCharts (SVG output) over Chart.js (canvas) specifically because SVG is resolution-independent and embeds cleanly in a Playwright-generated PDF. No changes to chart code are expected.
- ADR-0010 documents the full set of PDF export design decisions from the grilling session: separate template, Celery async, PDFExport model, calculated ToC, US Letter, cover page structure, and header/footer spec.
- The Roadmap Overview is currently a static string constant in `reports/views.py` (`_ROADMAP_OVERVIEW`). The PDF template should reuse this same constant — it is not stored in the database.
- The PDF template URL (`reports/<uuid>/pdf/`) is an internal implementation detail. It should not be linked from the navigation or exposed in the UI; advisors interact only with the "Download PDF" button on the standard Report page.
- Playwright must be added as a server dependency (`playwright` Python package + `chromium` browser binary). This should be included in the deployment configuration.
