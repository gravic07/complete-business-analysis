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

## Comments

**How production served `MEDIA_URL` before this change:** Django never serves media in production (the `static()` media route in `config/urls.py` only applies when `DEBUG` is on). Nginx served all of `{{ media_url }}` (`/uploads/`) straight from `{{ media_root }}` (`/var/www/cba/mediafiles`) with public 30-day cache headers (`ansible/roles/nginx/templates/app.conf.j2`). PDF exports are stored by the default `FileSystemStorage` under `pdf_exports/`, so anyone who guessed `/uploads/pdf_exports/{Company}_{AssessmentName}_{YYYYMMDD}.pdf` could fetch it.

**What changed:**

- `ansible/roles/nginx/templates/app.conf.j2`: added `location ^~ {{ media_url }}pdf_exports/ { return 404; }`. It's a longer prefix than the general media location, and `^~` stops regex locations from overriding it, so nginx answers every request under `/uploads/pdf_exports/` with 404. Other media is still served as before. Storage location is unchanged, so existing files need no migration. The nginx role README documents the new rule.
- The only way to fetch a PDF now is `reports:pdf_download` (`/reports/pdf-export/<pk>/download/`). It requires login and Team membership, returns 404 unless the export is complete and has a file, and streams the file as an attachment under its stored friendly filename.
- The status endpoint's `download_url` and the Report page's "Re-download last PDF" link both point at the download view. The PDFExport admin page now shows the file name as text instead of linking to the dead media URL.

**To deploy:** `deploy.yml` only runs the `app` role, so the nginx change needs a `site.yml` run (or `site.yml` limited to the nginx role). Then check that `curl -I https://<domain>/uploads/pdf_exports/<existing file>.pdf` returns 404. This wasn't verified against a live server: neither nginx nor the server was reachable from the dev machine.
