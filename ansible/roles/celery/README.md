# Role: celery

Installs and starts the Celery worker and Celery Beat scheduler as systemd services.

## What this role does

1. Templates `celery-worker.service` to `/etc/systemd/system/`
2. Templates `celery-beat.service` to `/etc/systemd/system/`
3. Reloads systemd and enables/starts both services

## Services

### celery-worker

Runs the Celery task worker. Concurrency is auto-derived from available vCPUs.

Key settings:
- `--concurrency={{ celery_workers }}` — number of worker processes (calculated at runtime)
- `--time-limit={{ celery_task_time_limit }}` — hard task timeout in seconds (default 300)
- `KillMode=mixed` — on stop, SIGTERM propagates to child workers so in-flight tasks can finish; `TimeoutStopSec=60` gives them up to 60 seconds before SIGKILL

### celery-beat

Runs the Celery Beat scheduler using `django_celery_beat.schedulers:DatabaseScheduler`. Periodic task schedules are managed through the Django admin rather than hardcoded in settings. Beat is idle until periodic tasks are added via the admin.

## Variables (from `group_vars/all.yml`)

| Variable                | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `app_name`              | Celery app name (`-A {{ app_name }}`), resolves to `config` |
| `app_user` / `app_group`| OS user/group the services run as                   |
| `app_src`               | Working directory (`WorkingDirectory`)               |
| `app_env_file`          | Path to `.env` file loaded by both services          |
| `app_venv`              | Virtual environment root; binaries at `{{ app_venv }}/bin/` |
| `app_home`              | Base path for log files (`{{ app_home }}/logs/`)     |
| `celery_workers`        | Worker concurrency, auto-derived from vCPU count     |
| `celery_task_time_limit`| Hard task timeout in seconds (default 300)           |

## Dependencies

Requires the `app` role to have run first — the virtual environment and `.env` file must exist before these services start.
