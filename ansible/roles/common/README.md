# Role: common

Base server provisioning — packages, users, SSH hardening, firewall, dotfiles, and maintenance tooling. Always runs first; all other roles depend on the environment this establishes.

## What this role does

1. Updates apt cache and installs base packages (git, curl, zsh, build deps, libpq-dev, python3-pip, etc.)
2. Installs Neovim via snap and tree-sitter CLI via npm (for developer tooling)
3. Installs Node.js `{{ node_major_version }}` via NodeSource
4. Creates the `{{ app_group }}` and `sshusers` OS groups
5. Creates `{{ app_user }}` (app process identity) and `{{ admin_user }}` (human SSH user)
6. Deploys the SSH deploy key to both users' `~/.ssh/id_ed25519`
7. Grants `{{ admin_user }}` passwordless sudo
8. Hardens sshd: custom port, no root login, no password auth, restricts to `sshusers` group
9. Configures UFW: default-deny inbound, allows SSH / HTTP / HTTPS
10. Installs `maintenance-on` and `maintenance-off` scripts to `/usr/local/bin/`
11. Enables unattended security upgrades
12. Sets up dotfiles (bare repo) for both `{{ admin_user }}` and `{{ app_user }}`

## Files required before running

| File | Description |
| ---- | ----------- |
| `roles/common/files/deploy_key` | Private SSH key with read access to the app repo and dotfiles repo. Mode 600. **Not committed — add to `.gitignore`.** |

## Variables (from `group_vars/all.yml`)

| Variable           | Description                                           |
| ------------------ | ----------------------------------------------------- |
| `app_user`         | OS user that owns and runs the application (`django`) |
| `app_group`        | OS group for the app user                             |
| `app_user_home`    | Home directory for the app user                       |
| `admin_user`       | Human SSH user with sudo access                       |
| `admin_ssh_pubkey` | Public key added to the admin user's `authorized_keys`|
| `ssh_port`         | Non-default SSH port (default `2207`)                 |
| `node_major_version` | Node.js major version installed via NodeSource      |
| `dotfiles_repo`    | SSH URL of the dotfiles bare repo                     |
| `dotfiles_branch`  | Branch to check out                                   |

## SSH access model

- `{{ admin_user }}` — can SSH in (member of `sshusers`), has passwordless sudo
- `{{ app_user }}` — **cannot SSH in** (not in `sshusers`); use `sudo su - {{ app_user }}` from the admin account to access its environment for debugging

## Dotfiles

Uses a [bare repo approach](https://www.atlassian.com/git/tutorials/dotfiles): the repo is cloned as `~/.cfg` and files are checked out directly into the home directory. Applied to both `{{ admin_user }}` and `{{ app_user }}` so both have a consistent shell environment (zsh + Neovim config).

## Maintenance scripts

`maintenance-on` and `maintenance-off` create/remove `/etc/nginx/maintenance.flag`. Nginx checks for this flag and serves a static maintenance page when it exists. The `maintenance_ip` in `group_vars/all.yml` always bypasses the maintenance page for your IP.
