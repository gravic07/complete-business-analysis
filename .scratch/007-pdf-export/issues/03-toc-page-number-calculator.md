Status: complete

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

- [x] Module exists in the `reports` app with a clear public function signature
- [x] Given 7 categories, each section maps to the correct page number per the formula above
- [x] Given 1 category (minimum), all page numbers are correct
- [x] Given a different N (e.g. 5), all page numbers shift correctly
- [x] Unit tests cover at least N=1, N=7, and one intermediate value
- [x] Unit tests assert every section key is present in the returned mapping

## Implementation notes

- Module: `reports/utils/toc_calculator.py`
- Tests: `reports/tests/test_toc_calculator.py` (6 tests, all passing)
- Public signature: `calculate_toc_page_numbers(categories: list[str], name: str) -> dict[str, int]`
- Category entries are prefixed to avoid collisions: `"analysis:{cat}"` and `"recommendations:{cat}"`
- Cover Page and Table of Contents are excluded from the returned mapping
- The `name` parameter personalizes the Analysis header key (e.g. `"Analysis for Testing 2"`)

## Blocked by

None — can start immediately.
