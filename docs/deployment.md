# Deployment (reference instance)

Operator notes for the CI/CD pipeline and the reference deployment ([finitum.app](https://finitum.app), a VPS). Self-hosters don't need any of this -- `docker compose up --build` per the [README](../README.md) is enough; this doc describes how the hosted instance ships.

## Pipeline

Every push to `main` runs [.github/workflows/ci.yml](../.github/workflows/ci.yml):

1. **lint-test** -- `ruff check` + `pytest` (also runs on pull requests, as a gate).
2. **build-push** -- builds a locked image (`uv.lock` + `uv sync --frozen`) and pushes `ghcr.io/richardhapb/finitum-api` tagged `latest` and `sha-<sha>`. The immutable sha tag is what deploys.
3. **build-web** -- runs only when `web/**` (or the workflow itself) changed: builds the static frontend with Bun (`VITE_API_URL` from the `WEB_API_URL` repo variable -- public by nature, it's baked into the shipped bundle) and uploads it as a tarball artifact.
4. **deploy** -- SSHes into the VPS as a low-privilege deploy user. If there's a web build, it is first scp'd (no sudo) to a fixed path in the deploy user's home. Then:

   ```bash
   sudo /usr/local/sbin/finitum-deploy "$IMAGE_TAG"
   sudo /usr/local/sbin/finitum-deploy --web   # only when the frontend changed
   ```

All environment-specific detail (paths, users, the compose invocation) lives in the root-owned `finitum-deploy` script on the server -- the public workflow file contains no infrastructure information. The script validates the image tag, does `git pull --ff-only` as the app user (only compose/config files come from git; app code lives in the image), then `docker compose pull` + `up -d` with `IMAGE_TAG` exported, and prunes only this repo's images. Prod uses `volumes: !reset []` so no host source is mounted -- the server runs exactly what CI built.

The `--web` mode publishes the frontend: it reads the tarball only from its fixed expected path (arguments never carry paths across the sudo boundary), refuses archives without an `index.html`, stages next to the web root, and swaps directories atomically, keeping the previous build as an instant-rollback backup.

## Security model

- The application files are owned by a dedicated **app user** with `nologin` -- nobody can SSH in as it, and its `.env` files are mode 0600.
- CI authenticates as a separate **deploy user** whose sudoers entry permits exactly one command: the `finitum-deploy` script. A leaked deploy key can trigger a deploy and nothing else. Its SSH key is restricted (`no-port-forwarding,no-agent-forwarding,no-X11-forwarding`).
- The deploy script whitelists tags (`latest` or `sha-<hex>`), so arguments can't be used to smuggle commands across the sudo boundary.
- The server repo's `origin` uses HTTPS (anonymous read-only -- the repo is public), so no GitHub credentials exist on the box.

## One-time setup

- **Repository secrets** (Settings → Secrets and variables → Actions): `HOST_ADDRESS`, `HOST_USER` (the deploy user), and `HOST_SSH_KEY` (its private key).
- **On the server** (as root): create the `nologin` app user owning the app directory (clone the repo there on `main` over HTTPS, populate `.env.prod`; back up `CREDENTIALS_ENCRYPTION_KEY` -- losing it makes stored Google tokens unrecoverable); install `finitum-deploy` to `/usr/local/sbin` (root-owned, mode 0700) with the app path/user set inside; create the deploy user with the restricted authorized_keys entry and a sudoers file allowing only that script (`visudo -cf` it). Confirm `docker compose version` ≥ 2.24 (required for `!reset`).
- **Smoke test** without deploying: `sudo /usr/local/sbin/finitum-deploy latest --check` (validates git access and compose config, changes nothing).

## Email worker

Inbound email relies on the Cloudflare Email Routing worker in [infra/email-worker/](../infra/email-worker/) deployed on the ingest domain, sharing `INGEST_WEBHOOK_SECRET` with the API. See that directory's README for setup.
