# Assessment gains a draft/in_progress/complete status instead of being created atomically

Previously, an `Assessment` was created only once, atomically, when the advisor submitted a single form containing the client selection and every answer at once — there was no notion of an incomplete Assessment. To support a per-Category Guidance step that must be enterable *before* any questions are answered, an Assessment must now exist before its answers do.

We decided to give `Assessment` an explicit `status` field (`draft → in_progress → complete`), created as soon as the advisor selects a Client and AssessmentTemplate. `complete` is set only by an explicit advisor action ("Mark Complete"), never inferred from finishing a step, and requires both the Guidance step and all questions to be done. Only at `complete` does the Assessment become immutable and trigger its first Analysis — mirroring today's "submit → autostart" behavior, just decoupled from "last question answered."

The alternative considered was a session-backed multi-step form (nothing hits the database until a final atomic save, same as today's single-request model, just spread across two pages). This was rejected because planned future work adds further steps to assessment intake that need to happen across different machines and different users — session-backed state doesn't survive that handoff, but a persisted Assessment with a status does.

## Consequences

- The Guidance step and the questions step can be completed in either order; nothing enforces their sequence, only that both must be done before Complete.
- Existing Assessments (all fully answered) are backfilled to `status=complete` with `guidance_submitted_at=created_at`, so they don't appear to be missing a step that didn't exist when they were created.
- Incremental per-answer autosave (saving answers one at a time rather than one atomic submit) was explicitly deferred — this ADR only establishes that Assessment can persist mid-flight, not that answering itself becomes incremental. That is expected as an immediate follow-up.
