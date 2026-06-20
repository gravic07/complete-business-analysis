Status: done

# PDF template and view

## What to build

A dedicated Django view and HTML template that Playwright will render to produce the PDF. This is an internal URL the advisor never navigates to directly — Playwright loads it server-side during PDF generation.

The view assembles the same report data as the existing `ReportView` (executive summary, category sections, recommendations, roadmap, chart data, scores) plus the ToC page map from the calculator built in issue 03. It renders a standalone HTML template — no base layout, no navigation, no feedback form.

The template renders all PDF sections in sequence, with CSS `page-break-before: always` between sections. The first page (cover) uses `@page :first { margin: 0; }` to suppress header/footer. All other pages have space reserved for Playwright's injected header/footer.

**Sections in order:**
1. Cover Page — Peak Performance Partners logo, cover background image, "Complete Business Report" title, client business name, Assessment name, date prepared
2. Table of Contents — section names with page numbers from the ToC calculator
3. Score Overview — intro paragraph, large CBA Score, `categories-pie-chart.png` (static), per-category score list
4. Visualizations — ApexCharts bar chart (Category Scores) and radar chart (Holistic Business Visualization), using the same inline JSON injection pattern as the existing web report
5. Analysis: Executive Summary
6. Analysis: one page per category — category name as heading, then Overview, Impact, Path Forward sub-sections
7. Recommendations: Overview
8. Recommendations: one page per category — category name as heading, numbered list of 7 recommendations
9. Roadmap: Overview — static boilerplate text (reuse the `_ROADMAP_OVERVIEW` constant from the existing view)
10. Roadmap: Month 1–12 — one page per month with Goals, Action Items, Challenges
11. Potential Challenges
12. Post-Implementation Outcomes
13. Closing Reflections

For authentication during this issue, use a simple localhost-only bypass (allow unauthenticated requests from 127.0.0.1). The signed-token approach is introduced in issue 05.

The template is verifiable by visiting the URL directly in a browser with a logged-in session and inspecting the rendered HTML.

## Acceptance criteria

- [x] URL `reports/<uuid>/pdf/` renders the full PDF template without error for an Assessment with a complete Analysis
- [x] Cover page displays logo, cover image, client name, Assessment name, and formatted date
- [x] Table of Contents lists all sections with the correct page numbers from the ToC calculator
- [x] Score Overview displays the total CBA score and per-category scores
- [x] `categories-pie-chart.png` appears on the Score Overview page
- [x] ApexCharts bar and radar charts render on the Visualizations page
- [x] All category Analysis sections appear (Executive Summary first, then one per category)
- [x] All category Recommendations sections appear (Overview first, then one per category)
- [x] All 12 Roadmap months appear, each with Goals, Action Items, and Challenges
- [x] Potential Challenges, Post-Implementation Outcomes, and Closing Reflections appear
- [x] No navigation, feedback form, or non-PDF chrome appears in the template
- [x] CSS page breaks are present between sections

## Blocked by

- `01-schema-foundation.md` — needs `Assessment.name`
- `02-static-asset-migration.md` — needs static image paths
- `03-toc-page-number-calculator.md` — needs ToC calculator
