# ApexCharts chosen over Chart.js; Playwright targeted for PDF export

The report page displays two charts — a bar chart and a radar chart — showing each category's score as a percentage of its maximum possible score. We chose ApexCharts over Chart.js as the charting library, and Playwright as the planned PDF export mechanism.

## Chart library: ApexCharts over Chart.js

Chart.js renders to a `<canvas>` element (raster). ApexCharts renders SVG (vector). This distinction matters because a planned PDF export feature needs charts that reproduce faithfully at print DPI without a separate capture step.

With a canvas-based library, exporting a chart to PDF requires calling `chart.toBase64Image()` to capture a PNG snapshot and embedding it — an extra step that also produces a raster image that can look soft at high DPI. SVG is resolution-independent and embeds directly into any HTML-to-PDF pipeline without conversion.

Chart.js was the obvious default choice (simpler API, wider adoption), but the PDF export requirement was the deciding factor. The two libraries are otherwise comparable for bar and radar chart use cases.

## PDF export: Playwright (headless browser)

The report page combines Bulma CSS layout, Django-rendered HTML, and JavaScript-executed ApexCharts SVG. A server-side HTML-to-PDF library (e.g. WeasyPrint) cannot execute JavaScript — so ApexCharts would never render, regardless of the SVG output format. A headless browser is therefore required.

Playwright renders the full page including all JavaScript, captures the live DOM (including rendered SVG charts), and produces a print-quality PDF. It also handles Bulma layout, custom fonts, and dynamic content without special-casing.

The alternative — serializing the rendered SVG out of the DOM and re-embedding it as static markup before passing to WeasyPrint — was rejected as brittle and complex for a report of this structure.

Playwright-based PDF export is not yet implemented; this ADR records the direction so the chart library choice is not revisited without this context.

## Consequences

- ApexCharts is loaded via CDN on the report page only (not globally).
- Chart data is injected as inline JSON at render time; no separate API call is made.
- When Playwright-based export is implemented, no changes to chart code are expected — the headless browser renders the same page the advisor sees.
