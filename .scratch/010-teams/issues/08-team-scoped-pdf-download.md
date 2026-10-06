# 08 — Team-scoped PDF download

**What to build:** A generated PDF Report can only be downloaded by a logged-in member of the owning Team — never from a public, guessable URL. Add a download view (e.g. `reports:pdf_download`, keyed by PDFExport pk) that looks the export up via `PDFExport.objects.for_team`, returns 404 if it's absent or not complete, and streams the file with `FileResponse` as an attachment using the existing friendly filename. The PDF export status endpoint and the Report page link to this view instead of the raw media URL. Then stop production serving the PDF export media directory publicly: check how production serves `MEDIA_URL` today and either exclude the PDF exports path from public serving or move PDF exports to non-public storage, recording what was changed in a comment on this ticket. See PRD § PDF download; user stories 32–34.

**Blocked by:** 07 — Scope Reports, Analysis and PDF exports to the Team.

**Status:** ready-for-agent

- [ ] A member of the owning Team downloading a complete PDFExport gets the file with `Content-Disposition: attachment` and the friendly filename.
- [ ] A member of another Team gets 404; an anonymous request redirects to login; a User with no Team is redirected to the no-team page (if ticket 04 has landed).
- [ ] A PDFExport that isn't complete returns 404.
- [ ] The PDF export status response and the Report page use the download view's URL; no template or response exposes the raw media URL of a PDF.
- [ ] In production, requesting a PDF by its old public media path no longer returns the file. The change made (web server config, storage location, etc.) is recorded under `## Comments` on this ticket.
- [ ] Tests (Django test client) cover the owning Team download, other-Team 404, anonymous redirect, and incomplete export 404.
- [ ] Full test suite passes.
