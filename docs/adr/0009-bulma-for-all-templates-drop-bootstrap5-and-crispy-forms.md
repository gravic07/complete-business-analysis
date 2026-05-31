# 0009 — Bulma for all templates; drop Bootstrap5 and crispy-forms

Date: 2026-05-31
Status: Accepted

## Context

The project uses Bulma as its CSS framework throughout the main application. The
django-allauth templates and the user profile form were originally scaffolded with
Bootstrap5 classes (via `django-crispy-forms` and `crispy-bootstrap5`), but Bootstrap5
CSS was never loaded in `base.html`. This left login, logout, and profile-edit pages
completely unstyled.

## Decision

Convert all allauth element and layout templates to Bulma. Replace `{{ form|crispy }}`
in `users/user_form.html` with manual Bulma field rendering using `django-widget-tweaks`.
Remove `django-crispy-forms` and `crispy-bootstrap5` from the project entirely.

## Alternatives considered

- **Load Bootstrap5 alongside Bulma** — avoids template rewrites but doubles the CSS
  payload and requires maintaining two conflicting utility class namespaces.
- **Use crispy-bulma** — a third-party crispy pack for Bulma exists but is not actively
  maintained and adds an extra dependency for something that can be done directly.

## Consequences

- All allauth-rendered pages (login, password reset, MFA, account management) and the
  user profile form now use consistent Bulma styling.
- `django-widget-tweaks` is added as a dependency for rendering form fields with Bulma
  classes in templates that receive a full Django form object.
- Two packages removed: `django-crispy-forms`, `crispy-bootstrap5`.
