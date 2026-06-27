# Role: gunicorn

Installs and starts the Gunicorn WSGI server as a systemd service, bound to a Unix socket.

## What this role does

1. Templates `gunicorn-{{ project_name }}.service` to `/etc/systemd/system/`
2. Reloads systemd and enables/starts the service

## Service

Runs `config.wsgi:application` under the `{{ app_user }}` account. Key settings:

- `--bind unix:/run/gunicorn/{{ project_name }}.sock` — Unix socket (nginx proxies to this)
- `--workers {{ gunicorn_workers }}` — worker count auto-derived from available vCPUs
- `--timeout 60` — kills a worker that takes longer than 60 s to respond
- `KillSignal=SIGQUIT` — graceful stop: gunicorn finishes in-flight requests before shutting down
- `RuntimeDirectory=gunicorn` — systemd creates `/run/gunicorn/` at start, owned by `{{ app_user }}`; no manual directory setup needed

## Variables (from `group_vars/all.yml`)

| Variable           | Description                                                              |
| ------------------ | ------------------------------------------------------------------------ |
| `project_name`     | Used in the service filename (`gunicorn-{{ project_name }}.service`) and socket path |
| `app_name`         | WSGI module prefix (`config`) — becomes `config.wsgi:application`        |
| `app_user` / `app_group` | OS user/group the service runs as                               |
| `app_src`          | Working directory (`WorkingDirectory`)                                   |
| `app_env_file`     | Path to `.env` file loaded by the service                                |
| `app_venv`         | Virtual environment root; gunicorn binary at `{{ app_venv }}/bin/gunicorn` |
| `app_home`         | Base path for log files (`{{ app_home }}/logs/`)                         |
| `gunicorn_workers` | Worker count, auto-derived from vCPU count at runtime                    |
| `gunicorn_bind`    | Bind address — `unix:/run/gunicorn/{{ project_name }}.sock`              |

## Dependencies

Requires the `app` role to have run first — the virtual environment must exist before this service starts.
