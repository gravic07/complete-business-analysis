# PDF export: separate template, Celery async, PDFExport model, calculated ToC page numbers

PDF export was designed to produce a multi-section, print-quality PDF from a finished Report. Several interconnected decisions were made together.

## Separate PDF template over print CSS

The web report uses a tab-based layout (Analysis / Recommendations toggled per category). The PDF requires a completely different section order: all Analysis sections together, then all Recommendations sections together, preceded by a cover page, table of contents, and score overview that have no equivalent in the web template.

CSS `@media print` rules can show hidden elements but cannot reorder DOM nodes across sections. Embedding a second print-only layout inside `report-detail.html` would effectively be writing a second template inside the first.

A dedicated template at `reports/<uuid>/pdf/` was chosen instead. Playwright loads this URL server-side — the advisor never navigates to it directly. The advisor clicks "Download PDF" on the report page and receives the file.

## Async delivery via Celery + polling

Playwright rendering takes several seconds. A synchronous Django view would block the request for the full render duration.

Async Celery + polling was chosen, consistent with how Analysis generation already works in this project. The advisor clicks "Download PDF," a Celery task is queued, and the UI polls until the job completes and triggers the download. This keeps the UX responsive and the pattern familiar.

## PDFExport model for job tracking

Polling requires a persistent record to query against. A `PDFExport` model was added to the `reports` app with `assessment` FK, `status` (pending/processing/complete/failed), and a `file` FileField. This mirrors the `Analysis` status pattern exactly. Storing the file also enables re-downloading the last PDF without re-generating it.

A Redis/cache-only approach (task ID in session) was rejected because it gives no persistent download link and is harder to debug on failure.

## Calculated page numbers for the Table of Contents

Accurate page numbers in a Playwright PDF require knowing how many pages each section occupies before rendering the ToC — a chicken-and-egg problem. Two-pass generation (render once to measure, render again with numbers) was considered but doubles render time and complexity.

Most sections in this report are exactly one page (each category analysis, each category recommendations page, each roadmap month). Page numbers are calculated from the known structure with a fixed offset. Variable-length sections (Executive Summary, Recommendations Overview, Potential Challenges, Post-Implementation Outcomes, Closing Reflections) may occasionally cause subsequent page numbers to be off by one or more.

Two-pass generation is the planned upgrade path if miscalculations prove too frequent in practice.

## PDF format and layout

- **Page size:** US Letter (8.5" × 11")
- **Header:** dark navy bar — Assessment name (uppercased) left, client business name right. Excluded from cover page only.
- **Footer:** dark navy bar — page number left, "COMPLETE BUSINESS REPORT" right. Excluded from cover page only.
- **PDF sections in order:** Cover Page, Table of Contents, Score Overview, Visualizations, Analysis, Recommendations, Roadmap (Overview + 12 months + Potential Challenges + Post-Implementation Outcomes + Closing Reflections)
- **Score Overview:** uses static `categories-pie-chart.png` for now; planned to become a dynamic ApexCharts visualization in a future update.

## Consequences

- Playwright must be installed as a server-side dependency.
- A `PDFExport` model and migration are required.
- A `name` field is added to `Assessment` (editable on the Report page, defaults to "Initial Report") and appears on the PDF cover page and header.
- Static assets (`cover-bg-img.jpg`, `categories-pie-chart.png`) should be moved from the repo root to `static/images/`.
- The PDF template is a separate maintenance surface from the web report template.
