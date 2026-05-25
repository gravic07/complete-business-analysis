# Complete Business Analysis Tool

A tool for analyzing the strengths and weaknesses of a business and building a plan for success.

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Tech Stack

- **Backend:** Django 6.0, Django REST Framework, Celery
- **Database:** PostgreSQL
- **Cache / Broker:** Redis
- **Frontend:** Sass, BrowserSync
- **Python:** 3.14 managed by uv

## Django Applications

A **Client** is the top-level entity. An **Assessment** is completed for a client using a reusable template of weighted, categorized questions. The **Analysis** app processes the answered questions into scored, category-level insights, and the **Reports** app turns those insights into a presentable business analysis report. The **core** and **users** apps underpin the whole system.

| App | Purpose |
|---|---|
| `core` | Provides the abstract `BaseModel` (UUID primary key, `created_at`, `updated_at`) inherited by every other app's models. |
| `users` | Custom user model with email-based authentication, extending Django's `AbstractUser`. |
| `clients` | Stores client businesses and their primary contact; the top-level entity that assessments are run against. |
| `assessments` | Owns assessment templates (sets of weighted, categorized questions) and records completed assessments with per-answer snapshots linked to a client. |
| `analysis` | Processes completed assessment answers to produce scored, category-level insights. |
| `reports` | Generates and presents the business analysis report from scored assessment data. |

See [Assessment-to-Report Flow](docs/assessment-to-report-flow.md) for a deep-dive on the full analysis pipeline, including the Mermaid diagram, model reference, and stage-by-stage function walkthrough.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js](https://nodejs.org/) (for frontend tooling)
- PostgreSQL running locally
- Redis running locally

## Installation

1. Clone the repo and navigate to the project root.

2. Install Python dependencies:

       uv sync

3. Install Node dependencies:

       npm install

4. Copy the example env file and configure it:

       cp .env.example .env

5. Create the database and run migrations:

       uv run python manage.py migrate

6. Load the CBA question data:

       uv run python scripts/create_cba_model_instances.py

7. Create a superuser:

       uv run python manage.py createsuperuser

## Running the Dev Server

`npm run dev` starts three processes in parallel:

- Django dev server at `http://localhost:8000`
- Sass compiler (watches `static/sass/` and outputs compressed CSS)
- BrowserSync proxy at `http://localhost:3000` with live reload on CSS and template changes

Because the npm scripts call `python` directly, the virtual environment must be active first:

```bash
source .venv/bin/activate
npm run dev
```

Open `http://localhost:3000` in your browser.

## Common Commands

### Tests

    uv run pytest

### Test coverage

    uv run coverage run -m pytest
    uv run coverage html
    open htmlcov/index.html

### Type checking

    uv run mypy complete_business_analysis_tool

### Linting and formatting

Pre-commit hooks run Ruff, djLint, and pyproject-fmt automatically on commit. To run manually:

    uv run pre-commit run --all-files

## Celery

In development, Celery tasks run eagerly (synchronously) — no worker needed.

In production, start a worker from the project root:

```bash
uv run celery -A config.celery_app worker -l info
```

To run periodic tasks, start the beat scheduler:

```bash
uv run celery -A config.celery_app beat
```

## Settings

Settings are split by environment under `config/settings/`:

| File | Used when |
|---|---|
| `local.py` | Local development (default) |
| `test.py` | Test suite |
| `production.py` | Production deployment |

Key production environment variables: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `MAILGUN_API_KEY`, `SENTRY_DSN`.
