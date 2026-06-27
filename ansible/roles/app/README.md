# Role: app

Deploys the CBA Django application onto the server. Runs as root but switches to `{{ app_user }}` for all application-level operations.

## What this role does

1. Installs `uv` system-wide via pip
2. Pre-fetches `{{ python_version }}` via `uv python install`
3. Creates the app home directory (`{{ app_home }}`)
4. Clones or updates the app repo to `{{ app_src }}`
5. Creates `logs/` and `data/` subdirectories
6. Installs Python dependencies via `uv sync --frozen` (requires a committed `uv.lock`)
7. Templates the `.env` file to `{{ app_env_file }}`
8. Runs Django migrations (`manage.py migrate --noinput`)
9. Creates static and media directories under `/var/www/`
10. Collects static files (`manage.py collectstatic`)

## Variables (from `group_vars/all.yml`)

| Variable        | Example value              | Description                              |
| --------------- | -------------------------- | ---------------------------------------- |
| `app_user`      | `django`                   | OS user that owns and runs the app       |
| `app_group`     | `django`                   | OS group for the app user                |
| `app_home`      | `/home/django/cba`         | Root directory for the deployment        |
| `app_src`       | `{{ app_home }}`           | Git clone destination (repo root)        |
| `app_venv`      | `{{ app_home }}/.venv`     | Virtual environment path (created by uv) |
| `app_env_file`  | `{{ app_home }}/.env`      | Environment file path                    |
| `app_repo`      | `git@github.com:org/r.git` | SSH URL of the application repo          |
| `app_branch`    | `master`                   | Branch to deploy                         |
| `python_version`| `3.14`                     | Python version managed by uv             |
| `app_name`      | `config`                   | Django project package name              |
| `static_root`   | `/var/www/cba/staticfiles` | collectstatic output directory           |
| `media_root`    | `/var/www/cba/mediafiles`  | User-uploaded media directory            |

## Vault variables (required)

These must be defined in an Ansible vault file — see the top-level README for setup instructions.

| Variable          | Description                                      |
| ----------------- | ------------------------------------------------ |
| `django_secret_key` | Django `SECRET_KEY`                            |
| `postgres_password` | PostgreSQL password for `{{ postgres_user }}`  |
| `django_admin_url`  | URL path for the Django admin (e.g. `secret-admin/`) |
| `mailgun_api_key`   | Mailgun API key for transactional email        |
| `mailgun_domain`    | Mailgun sender domain                          |
| `vault_sentry_dsn`  | Sentry DSN (optional — omit to disable Sentry)|
| `claude_api_key`    | Anthropic API key (optional)                   |

## Handlers

- **Restart gunicorn** — triggered when the repo or `.env` changes
- **Restart celery** — triggered when the repo or `.env` changes
