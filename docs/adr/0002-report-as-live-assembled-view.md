# Report is a live view assembled from the latest ReportSection per category

A Report is not stored as a monolithic document tied to a single Analysis run. Instead, it is assembled at render time by taking the latest ReportSection per Category across all Analysis runs for an Assessment.

This decision is driven by the partial re-analysis feature: when an advisor gives feedback on only one category, only that category is reanalyzed and a new ReportSection is created for it. The other categories should show their most recently generated content without being regenerated. Storing Reports as snapshots would require either copying unchanged sections (data duplication) or a complex inheritance chain to fill in the gaps from prior runs. The live-assembly model avoids both: the Report is always current by construction, and ReportSections are the durable artifacts.

## Consequences

- There is no single "Report" record in the database — a Report is a query result, not a row
- The assembled Report can change if an earlier Analysis run's ReportSection is somehow superseded — but since Analysis runs are append-only and ReportSections are never updated, this is safe
- Displaying the full Report requires one query per category to find the latest ReportSection; this can be done efficiently with a single query using `DISTINCT ON` or a subquery
