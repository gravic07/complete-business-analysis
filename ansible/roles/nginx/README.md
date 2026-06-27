# Role: nginx

Installs Nginx as a reverse proxy, configures SSL via Let's Encrypt, and enables maintenance mode support.

## What this role does

1. Installs `nginx`, `certbot`, and `python3-certbot-nginx`
2. Deploys `snippets/ssl-params.conf` (TLS hardening, HSTS, security headers)
3. Removes the default Nginx site
4. Templates the app vhost to `/etc/nginx/sites-available/{{ project_name }}.conf` and symlinks it to `sites-enabled/`
5. Ensures Nginx is running and enabled
6. Obtains a Let's Encrypt certificate (skipped if cert already exists)

## Vhost behaviour

- HTTP (port 80) → permanent 301 redirect to HTTPS, preserving subdomains
- HTTPS (port 443) — main server block:
  - Static files (`{{ static_url }}`) — aliased from `{{ static_root }}/`, 30-day cache headers
  - Media files (`{{ media_url }}`) — aliased from `{{ media_root }}/`, 30-day cache headers
  - `/favicon.ico` — served directly from `{{ static_root }}/favicon/`
  - `/api/` and `/` — proxied to the Gunicorn Unix socket with `no-store` cache headers
  - Maintenance mode — checked via `/etc/nginx/maintenance.flag`; `{{ maintenance_ip }}` always bypasses it

## Maintenance mode

Nginx checks for the flag file on every request. The `maintenance-on` / `maintenance-off` scripts (installed by the `common` role) create and remove it. `deploy.yml` calls these automatically around code deploys. `{{ maintenance_ip }}` always sees the live site, not the maintenance page.

## Variables (from `group_vars/all.yml`)

| Variable          | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `project_name`    | Used in vhost filename (`{{ project_name }}.conf`) and Gunicorn socket path |
| `domain_name`     | Primary domain; used for `server_name`, SSL cert, and HSTS               |
| `admin_email`     | Email passed to `certbot` for Let's Encrypt notifications                |
| `gunicorn_bind`   | Upstream socket (`unix:/run/gunicorn/{{ project_name }}.sock`)           |
| `static_url`      | URL prefix for static files (default `/assets/`)                         |
| `static_root`     | Filesystem path Nginx aliases for static files                           |
| `media_url`       | URL prefix for media uploads (default `/uploads/`)                       |
| `media_root`      | Filesystem path Nginx aliases for media files                            |
| `maintenance_ip`  | IP that bypasses the maintenance page                                    |

## Notes

- DNS must point at the server before the first run or the Let's Encrypt ACME challenge will fail.
- The certbot task uses `creates:` so it only runs once; subsequent deploys skip it (cert renewal is handled by certbot's own systemd timer).
- SSL hardening (cipher suites, HSTS, OCSP stapling) lives in `ssl-params.conf.j2` and is included via `snippets/ssl-params.conf`.
