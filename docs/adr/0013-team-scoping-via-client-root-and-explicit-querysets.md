# Team ownership lives on the Client; scoping is enforced by explicit querysets

To isolate data between Teams, we store a `team` FK on `Client` only and treat the Client as the ownership root: Assessments, Analysis runs, Reports, Feedback, PDFExports and ClientAccessLinks belong to a Team solely through their Client (`assessment.client.team`). Visibility is decided by that stamped `team`, never by `created_by` — `created_by` is an audit field. Scoping is enforced explicitly: each Team-owned model's queryset exposes `for_team(team)`, views look objects up through it, and a record from another Team returns 404 rather than 403. Every Team-scoped view has a test asserting a 404 for another Team's user.

## Considered Options

- **Derive the Team from the creator (`record.created_by.team`)** — rejected because ownership would silently move whenever an advisor changed Teams, and records would be orphaned if their creator lost their Team. The Team owns the data, not the person.
- **Denormalise `team` onto Assessment (and further down)** — rejected because two copies of the Team can disagree; with a single root an Assessment can never belong to a different Team than its Client, and moving a Client in Django admin moves everything downstream for free.
- **Automatic scoping via a default manager reading the current Team from thread-local/request state (django-scopes style)** — rejected because Celery tasks, the Playwright PDF render hop, beat sweeps and Django admin all run without a request Team and would each need an explicit escape hatch. Explicit `for_team()` calls are greppable and fit the existing `get_object_or_404` style; the per-view 404 tests are what catch a missed call.

## Consequences

- Every new view touching Team-owned data must scope its lookups; forgetting is a data leak, so the 404 test is mandatory, not optional.
- Downstream queries pay a join through `client` to filter by Team. Acceptable at current scale.
- Background work (Celery tasks, beat sweeps, the signed-token PDF path) remains Team-agnostic by design — it only ever acts on pks handed to it by an already-scoped view.
- Generated PDF files are no longer served from public `MEDIA_URL`; they are downloaded through a Team-scoped view, since a public media URL bypasses every check above.
- `LoginRequiredMiddleware` is enabled site-wide so an unscoped, unauthenticated view can't exist by omission; public entry points (allauth, client portal, the PDF signed-token path) opt out explicitly.
