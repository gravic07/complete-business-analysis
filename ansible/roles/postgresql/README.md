# Role: postgresql

Installs PostgreSQL and creates the application database and user.

## What this role does

1. Installs `postgresql-{{ postgres_version }}` and `postgresql-contrib`
2. Installs `python3-psycopg2` (required by Ansible's `community.postgresql` modules)
3. Ensures PostgreSQL is started and enabled
4. Creates the application database with UTF-8 encoding and `en_US.UTF-8` locale
5. Creates the application database user with the vault-supplied password
6. Grants all privileges on the database to the app user
7. Grants all privileges on the `public` schema to the app user (required in PostgreSQL 15+ where `PUBLIC` no longer has CREATE on the public schema by default)

## Variables (from `group_vars/all.yml`)

| Variable           | Description                              |
| ------------------ | ---------------------------------------- |
| `postgres_version` | PostgreSQL major version to install (17) |
| `postgres_db`      | Database name (`cba`)                    |
| `postgres_user`    | Database user (`cba`)                    |
| `postgres_host`    | Host Django connects to (`localhost`)    |
| `postgres_port`    | Port Django connects to (`5432`)         |

## Vault variables (from `group_vars/all/vault.yml`)

| Variable            | Description               |
| ------------------- | ------------------------- |
| `postgres_password` | Password for the app user |

## Notes

- `python3-psycopg2` is the system-level psycopg2 used by Ansible's postgresql modules. The Django app uses `psycopg[c]` (psycopg3) installed in the virtualenv — these are separate.
- The database is created from `template0` (not `template1`) so that the encoding and locale can be set explicitly.
- The `community.postgresql` collection must be installed: `ansible-galaxy collection install community.postgresql`.
