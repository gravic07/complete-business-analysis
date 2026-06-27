# Role: redis

Installs Redis and binds it to localhost for use as the Celery broker and cache backend.

## What this role does

1. Installs `redis-server`
2. Sets `bind {{ redis_bind }}` in `/etc/redis/redis.conf` (restricts Redis to localhost)
3. Ensures Redis is started and enabled

## Variables (from `group_vars/all.yml`)

| Variable     | Description                                   |
| ------------ | --------------------------------------------- |
| `redis_bind` | Interface Redis listens on (`127.0.0.1`)       |
| `redis_port` | Port Redis listens on (`6379`)                |

## Notes

- No `requirepass` is set — loopback binding is the security boundary. Redis is unreachable from outside the server, so a password would add complexity without meaningful benefit.
- Celery and Django connect via `REDIS_URL=redis://{{ redis_bind }}:{{ redis_port }}/0` (written to the app's `.env` file by the `app` role).
