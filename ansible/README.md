# Ansible — CBA Server Provisioning

Provisions and deploys the CBA Django stack on a single Ubuntu server.

## Stack

| Role         | What it installs / configures                                                                                        |
| ------------ | -------------------------------------------------------------------------------------------------------------------- |
| `common`     | Base packages, build deps, Neovim (snap), Node.js 22, users, SSH hardening, UFW, unattended-upgrades, dotfiles        |
| `postgresql` | PostgreSQL 17, database and user                                                                                     |
| `redis`      | Redis, bound to localhost                                                                                            |
| `app`        | uv, Python 3.14, uv deps, app repo, migrations, static files                                                         |
| `gunicorn`   | systemd service (`gunicorn-cba`) bound to a Unix socket                                                              |
| `celery`     | systemd services for the worker and celery-beat scheduler                                                            |
| `nginx`      | Reverse proxy with SSL, wildcard subdomains, maintenance mode                                                        |

**Services:** gunicorn (WSGI) → nginx; celery worker + beat → Redis broker; PostgreSQL on localhost.

---

## Before First Run

### 1. Ansible collections

Install the required Ansible collections before running any playbook:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

### 2. Deploy keys

Two separate deploy keys are required — GitHub does not allow the same public key to be registered as a deploy key on more than one repository.

**App repo key** (`roles/common/files/deploy_key`) — grants read access to `gravic07/complete-business-analysis`:

```bash
ssh-keygen -t ed25519 -C "cba-app-deploy" -f ~/.ssh/cba_app_deploy_key -N ""
# Add ~/.ssh/cba_app_deploy_key.pub → gravic07/complete-business-analysis → Settings → Deploy Keys (read-only)
cp ~/.ssh/cba_app_deploy_key ansible/roles/common/files/deploy_key
chmod 600 ansible/roles/common/files/deploy_key
```

**Dotfiles repo key** (`roles/common/files/dotfiles_deploy_key`) — grants read access to `gravic07/dotfiles`:

```bash
ssh-keygen -t ed25519 -C "cba-dotfiles-deploy" -f ~/.ssh/cba_dotfiles_deploy_key -N ""
# Add ~/.ssh/cba_dotfiles_deploy_key.pub → gravic07/dotfiles → Settings → Deploy Keys (read-only)
cp ~/.ssh/cba_dotfiles_deploy_key ansible/roles/common/files/dotfiles_deploy_key
chmod 600 ansible/roles/common/files/dotfiles_deploy_key
```

> Neither file is committed — both are in `.gitignore`.

### 3. Inventory

Two inventory files exist for the two distinct phases of deployment:

| File | When to use |
|------|-------------|
| `inventory/bootstrap.ini` | **First run only** — connects as `root` on port 22 (DigitalOcean Droplet defaults) |
| `inventory/production.ini` | **All subsequent runs** — connects as `gravic` on hardened port 2207 |

Set the real server IP in **both** files (`ansible_host=<REAL_SERVER_IP>`).

The `common` role creates the `admin` user, disables root login, and moves SSH to port 2207 — after that first run, `bootstrap.ini` can no longer connect.

### 4. `group_vars/all/main.yml`

Fill in the placeholder values before running:

| Variable          | Description                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------ |
| `app_repo`        | SSH URL of the application repo (`git@github.com:org/repo.git`)                            |
| `admin_ssh_pubkey`| Full public key for the admin user (paste the contents of `~/.ssh/id_ed25519.pub`)         |
| `admin_email`     | Email for Let's Encrypt certificate notifications                                          |
| `domain_name`     | Production domain (`cba.3-peak.com`)                                                       |
| `maintenance_ip`  | Your IP address — bypasses the maintenance page so you can verify the site while it's down |

**Worker tuning** (optional) — these have sensible defaults derived from `ansible_processor_vcpus` at runtime:

| Variable                | Default | Description                                    |
| ----------------------- | ------- | ---------------------------------------------- |
| `system_reserved_vcpus` | `2`     | vCPUs held back for OS, Redis, and Celery Beat |
| `celery_vcpu_divisor`   | `4`     | 1 Celery worker per N remaining vCPUs          |

On an 8-vCPU server the defaults produce 2 Celery workers and 9 Gunicorn workers.

### 5. Vault secrets

Sensitive values live in `group_vars/all/vault.yml`. This file is gitignored and never committed. Populate it with the real secrets before running:

```yaml
django_secret_key: "a-long-random-string"
postgres_password: "db-password"
django_admin_url: "your-secret-admin-path/"
vault_sentry_dsn: "https://...@sentry.io/..."   # omit or leave empty to disable Sentry
mailgun_api_key: "key-..."
mailgun_domain: "mg.cba.3-peak.com"
claude_api_key: "sk-ant-..."
```

The file is plain YAML (not encrypted) — keep it out of version control and off shared systems.

---

## Running the Playbooks

### Full provision (first time)

Provisions the entire server from scratch: packages, users, database, services, nginx, SSL, app code. Uses `bootstrap.ini` because root is the only user available on a fresh Droplet.

```bash
ansible-playbook -i inventory/bootstrap.ini site.yml
```

After this completes, root login is disabled and SSH moves to port 2207. All subsequent runs use `production.ini`.

### Code deploy

Pulls the latest app code, installs dependencies, runs migrations, collects static files, and restarts services. Puts the site into maintenance mode for the duration.

```bash
ansible-playbook -i inventory/production.ini deploy.yml
```

---

## After First Provision — Manual Steps

These steps are interactive and cannot be automated. Run them once per user after provisioning completes.

### Shell prompt (Powerlevel10k)

SSH in as each user and run:

```bash
p10k configure
```

Generates `~/.p10k.zsh` (machine-specific prompt config, not tracked in dotfiles). Without it the prompt renders unstyled.

### Neovim plugins

SSH in as each user who will use Neovim and launch it:

```bash
nvim
```

lazy.nvim bootstraps and installs all plugins automatically on first launch (~1 min). Afterwards run `:Mason` inside Neovim — it auto-installs the configured LSP servers (pyright, ts_ls, html, cssls). Node.js must be system-wide (handled by Ansible) for Mason to work; nvm alone is not sufficient because it is lazy-loaded and not in PATH at startup.

### SSL certificate

Certbot is run by Ansible during provisioning, but DNS must be pointing at the server before the playbook runs or the ACME challenge will fail.

---

## Maintenance Mode

The playbook installs `maintenance-on` and `maintenance-off` scripts at `/usr/local/bin/`. These create and remove a flag file (`/etc/nginx/maintenance.flag`) that nginx checks to serve the maintenance page.

```bash
sudo maintenance-on    # takes the site down
sudo maintenance-off   # brings the site back up
```

`deploy.yml` calls these automatically around the deploy sequence. Use them manually if you need to take the site down for other reasons.

The `maintenance_ip` variable in `group_vars/all/main.yml` is added to the nginx maintenance config so that IP always sees the live site, not the maintenance page — useful for verifying a deploy before bringing the site back up.

---

## Adding a Developer

Adding a second SSH user is a manual server operation — not in Ansible by design (one-time, low-frequency, simple).

```bash
# On the server as admin:
sudo adduser devname
sudo usermod -aG sshusers devname
sudo usermod -aG django devname
sudo mkdir -p /home/devname/.ssh
sudo nano /home/devname/.ssh/authorized_keys   # paste their public key
sudo chmod 700 /home/devname/.ssh
sudo chmod 600 /home/devname/.ssh/authorized_keys
sudo chown -R devname:devname /home/devname/.ssh
```

To grant passwordless sudo (optional):

```bash
echo 'devname ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/devname
sudo chmod 0440 /etc/sudoers.d/devname
sudo visudo -cf /etc/sudoers.d/devname
```
