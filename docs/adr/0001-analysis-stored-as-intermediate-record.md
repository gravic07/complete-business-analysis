# Analysis stored as a persistent intermediate record

Analysis is stored as a first-class model rather than computed on-the-fly from Assessment answers. Each time analysis is triggered — either on a fresh Assessment or in response to Feedback — a new Analysis record is created with its own status, scores, and linked ReportSections.

The alternative was to compute scores and call the AI at report-render time, discarding the results after display. We rejected this because the feedback cycle requires knowing what inputs (scores, question content, prior feedback) produced a given Report — without stored Analysis records, there is no audit trail and no way to explain why two Reports for the same Assessment differ. Storing Analysis also enables async processing via Celery (the AI call can take seconds to minutes) and lets the UI show a meaningful status while the job runs.

## Considered Options

- **Compute on-the-fly at render time** — rejected: no audit trail, blocks the request thread, incompatible with the feedback refinement cycle
- **Store only the final Report** — rejected: loses the intermediate inputs (scores, AI payload, feedback used) needed to understand and reproduce a given output
