# 01 — Client email field + ClientAccessLink schema & lifecycle helpers

**What to build:** The foundational schema and pure lifecycle logic every other ticket in this feature builds on: an optional email field on `Client`, the new `ClientAccessLink` model, and the Generate/Revoke/Regenerate/Is-valid helper functions that govern a link's life. No UI yet — this ticket is verified through tests, not a browser demo.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `Client` gains an optional, format-validated `email` field with no uniqueness constraint; existing `Client` rows are unaffected by the migration.
- [ ] `ClientAccessLink` model exists with an `assessment` FK, `link_type` (`guidance`/`answer`), a unique opaque `token`, and `status` (`active`/`revoked`); exactly one row is possible per `(assessment, link_type)`.
- [ ] Generate helper creates an active row with a fresh token only when no row exists yet, or the existing row is revoked.
- [ ] Revoke helper marks a row revoked without issuing a replacement token.
- [ ] Regenerate helper overwrites the token in place on an active row, leaving it active, discarding the prior token (no history kept).
- [ ] Is-valid helper reports invalid for a revoked link, invalid for an otherwise-active link whose parent Assessment is complete, and valid otherwise.
- [ ] Each of the above behaviors is covered by a direct test.
