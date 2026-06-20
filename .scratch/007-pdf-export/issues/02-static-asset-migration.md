Status: done

# Static asset migration: move cover and chart images to static/images/

## What to build

Two image files currently sit at the repo root and need to move to `static/images/` alongside the existing `company-logo.png` so they are served reliably by Django's static file pipeline during PDF generation.

Files to move:
- `cover-bg-img.jpg` → `complete_business_analysis_tool/static/images/cover-bg-img.jpg`
- `categories-pie-chart.png` → `complete_business_analysis_tool/static/images/categories-pie-chart.png`

Note: actual static dir is `complete_business_analysis_tool/static/images/` (alongside `company-logo.png`), not a root-level `static/`.

Update any references to these files in templates, CSS, or Python code to use the correct static file path. The PDF template (built in issue 04) will reference them from their new location.

## Acceptance criteria

- [x] `cover-bg-img.jpg` is in `static/images/` and no longer present at the repo root
- [x] `categories-pie-chart.png` is in `static/images/` and no longer present at the repo root
- [x] `python manage.py collectstatic` includes both files without error
- [x] No broken references remain in any template, CSS, or Python file

## Blocked by

None — can start immediately.
