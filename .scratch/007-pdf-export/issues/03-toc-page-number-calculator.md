Status: ready-for-agent

# ToC page number calculator

## What to build

A pure function module in the `reports` app that takes the number of categories in a report and returns a mapping of section name → page number. This mapping is passed to the PDF template to populate the Table of Contents.

The page structure is fixed for all reports:

```
1   — Cover Page
2   — Table of Contents
3   — Score Overview
4   — Visualizations
5   — Analysis: Executive Summary
6 … 5+N     — Analysis: one page per category (N categories, in order)
6+N         — Recommendations: Overview
7+N … 6+2N — Recommendations: one page per category
7+2N        — Roadmap: Overview
8+2N … 19+2N — Roadmap: Month 1–12
20+2N       — Potential Challenges
21+2N       — Post-Implementation Outcomes
22+2N       — Closing Reflections
```

The function accepts the ordered list of category names (to produce per-section keys) and the integer N (derived from that list). It returns a flat dict mapping every ToC entry to its page number.

This module has no database access and no Playwright dependency — it is a pure calculation.

## Acceptance criteria

- [ ] Module exists in the `reports` app with a clear public function signature
- [ ] Given 7 categories, each section maps to the correct page number per the formula above
- [ ] Given 1 category (minimum), all page numbers are correct
- [ ] Given a different N (e.g. 5), all page numbers shift correctly
- [ ] Unit tests cover at least N=1, N=7, and one intermediate value
- [ ] Unit tests assert every section key is present in the returned mapping

## Blocked by

None — can start immediately.
