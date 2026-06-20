Status: ready-for-agent

# Download PDF button, polling, and auto-download

## What to build

The complete end-to-end advisor-facing PDF export flow: button → trigger → Celery task (from issue 05) → polling → auto-download.

**"Download PDF" button** — displayed at the top of the Report page, adjacent to the Assessment name field (issue 06). Visible whenever the Assessment has at least one complete Analysis. Clicking it POSTs to the export trigger endpoint.

**Export trigger endpoint** — POST view at `reports/<uuid>/export-pdf/`. Creates a `PDFExport` record with status `pending`, queues the `generate_pdf_export` Celery task, and returns JSON `{pdf_export_id: "<uuid>"}`. The front end uses this ID to begin polling.

**Polling endpoint** — GET view at `reports/pdf-export/<uuid>/status/`. Returns JSON `{status, download_url}`. `download_url` is populated only when status is `complete`. The front end polls this endpoint every 2 seconds.

**Front-end polling loop** — after the button is clicked:
1. Button enters a loading/disabled state; a progress indicator is shown
2. Front end polls the status endpoint every 2 seconds
3. When status is `complete`, the browser follows `download_url` to trigger the file download, and the button returns to its normal state
4. When status is `failed`, polling stops, the progress indicator is replaced with an error message ("PDF generation failed — please try again"), and the button is re-enabled

**Re-download** — if the Assessment already has a `complete` `PDFExport`, show a secondary "Re-download last PDF" link below the button that goes directly to `download_url` without triggering a new generation.

## Acceptance criteria

- [ ] "Download PDF" button appears at the top of the Report page when at least one Analysis is complete
- [ ] "Download PDF" button is absent when no Analysis is complete
- [ ] Clicking the button creates a `PDFExport` record and queues the Celery task
- [ ] A progress indicator is shown while the PDF is generating
- [ ] The PDF downloads automatically when generation completes
- [ ] An error message is shown and the button re-enables when generation fails
- [ ] A "Re-download last PDF" link is shown when a complete `PDFExport` already exists
- [ ] The trigger endpoint returns 405 for non-POST requests
- [ ] The polling endpoint returns 404 for an unknown `PDFExport` UUID
- [ ] Django `TestCase` asserts trigger endpoint creates `PDFExport` and calls `generate_pdf_export.delay` (mocked)
- [ ] Django `TestCase` asserts polling endpoint returns correct JSON for `complete` and `failed` statuses

## Blocked by

- `05-pdf-service-and-celery-task.md` — needs the Celery task and PDFExport status transitions
- `06-assessment-name-inline-edit.md` — needs the Assessment name field visible on the page before the button is placed adjacent to it
