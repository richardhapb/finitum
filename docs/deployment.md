# Deployment (reference instance)

Operator notes for the CI/CD pipeline and the reference deployment ([finitum.app](https://finitum.app), a VPS). Self-hosters don't need any of this -- `docker compose up --build` per the [README](../README.md) is enough; this doc describes how the hosted instance ships.

## Pipeline

Every push to `main` runs [.github/workflows/ci.yml](../.github/workflows/ci.yml):

1. **lint-test** -- `ruff check` + `pytest` (also runs on pull requests, as a gate).
2. **build-push** -- builds a locked image (`uv.lock` + `uv sync --frozen`) and pushes `ghcr.io/richardhapb/finitum-api` tagged `latest` and `sha-<short>`.
3. **deploy** -- SSHes into the VPS and runs:

   ```bash
   cd ~/finitum
   git pull --ff-only
   docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   docker image prune -f
   ```

The image is self-contained (code + deps + alembic migrations baked in); `git pull` on the server only refreshes the compose/env files. Prod uses `volumes: !reset []` so no host source is mounted -- the server runs exactly what CI built.

## One-time setup

- **Make the package public**: GitHub → Packages → `finitum-api` → Package settings → Change visibility → **Public**. The server then pulls with no auth.
- **Add repository secrets** (Settings → Secrets and variables → Actions): `HOST_ADDRESS`, `HOST_USER`, and `HOST_SSH_KEY` (a private key whose public half is in the server's `~/.ssh/authorized_keys`).
- **On the server**: clone the repo to `~/finitum` on `main`, populate `.env.prod` (including `CREDENTIALS_ENCRYPTION_KEY` -- back it up, losing it makes stored Google tokens unrecoverable), and confirm `docker compose version` ≥ 2.24 (required for `!reset`).

## Email worker

Inbound email relies on the Cloudflare Email Routing worker in [infra/email-worker/](../infra/email-worker/) deployed on the ingest domain, sharing `INGEST_WEBHOOK_SECRET` with the API. See that directory's README for setup.
