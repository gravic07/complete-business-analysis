# Client Access Links use a persisted opaque token, not signed URLs or sessions

To let advisors send a Client a no-login link to fill in the Guidance step ("Concerns, Priorities and Goals") or the Answer Questions step remotely, we needed a link that stays valid for days and can be revoked early. We introduced a `ClientAccessLink` model — one row per `(Assessment, link_type)` — holding an opaque `secrets.token_urlsafe(32)` token as the URL identifier and an explicit `active`/`revoked` status, rather than reusing the existing `TimestampSigner`-based signed-URL pattern or trusting a session once the Client verifies their email.

## Considered Options

- **`TimestampSigner` (the existing pattern used for the PDF export's internal Playwright hop)** — rejected because a signed value can't be revoked before it expires, and the existing usage's 60-second `max_age` isn't suited to a link meant to stay valid for days. A persisted row is required to make "Revoke" take effect immediately.
- **Session-based email verification** — considered so a Client wouldn't have to retype their email on every page load, but rejected in favor of verifying live against `Client.email` on every load. No verified state is stored client-side or server-side between requests.
- **Admin-editable instructional copy** (a small settings/config model so advisors could edit the client-facing wording without a deploy) — considered, but rejected in favor of static template text; wording changes go through a normal developer/code-deploy cycle.

## Consequences

- A Client who refreshes mid-fill loses unsaved input and must re-verify their email; a `beforeunload`-style guard on the client-facing pages is the mitigation, not a persisted draft.
- Revoking a link takes effect on the Client's very next request, since validity is read from the persisted `status` on every load rather than trusted from an earlier check.
- Regenerating a link overwrites its token in place; no history of prior tokens is kept in v1.
