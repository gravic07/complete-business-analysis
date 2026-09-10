# 01 — Client email field + ClientAccessLink schema & lifecycle helpers

**What to build:** The foundational schema and pure lifecycle logic every other ticket in this feature builds on: an optional email field on `Client`, the new `ClientAccessLink` model, and the Generate/Revoke/Regenerate/Is-valid helper functions that govern a link's life. No UI yet — this ticket is verified through tests, not a browser demo.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `Client` gains an optional, format-validated `email` field with no uniqueness constraint; existing `Client` rows are unaffected by the migration.
- [x] `ClientAccessLink` model exists with an `assessment` FK, `link_type` (`guidance`/`answer`), a unique opaque `token`, and `status` (`active`/`revoked`); exactly one row is possible per `(assessment, link_type)`.
- [x] Generate helper creates an active row with a fresh token only when no row exists yet, or the existing row is revoked.
- [x] Revoke helper marks a row revoked without issuing a replacement token.
- [x] Regenerate helper overwrites the token in place on an active row, leaving it active, discarding the prior token (no history kept).
- [x] Is-valid helper reports invalid for a revoked link, invalid for an otherwise-active link whose parent Assessment is complete, and valid otherwise.
- [x] Each of the above behaviors is covered by a direct test.

## Comments

Implemented in `assessments/models.py` (`ClientAccessLink`), `assessments/services.py` (`generate_client_access_link`, `revoke_client_access_link`, `regenerate_client_access_link`, `is_client_access_link_valid`), and `clients/models.py` (`Client.email`). `is_client_access_link_valid` takes a `token` and resolves the link itself (returning `False` for an unrecognized token), matching the PRD's module contract for reuse by the future `client_portal` app. Migrations: `clients/0004_client_email.py`, `assessments/0006_clientaccesslink.py`. Marked `done` — awaiting review/merge; moving to ticket 02 is a separate decision.
