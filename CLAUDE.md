# Finitum

Open-source, dev-first personal finance manager: users forward their bank notification emails to a per-user ingest address, and Finitum parses them into transactions with community-written bank parsers.

## Project direction (read this first)

Finitum pivoted in July 2026 from a private, Chile-only SaaS to a **worldwide, open-source, dev-first project**. The goal is to become a world-class OSS standard for email-based transaction parsing, not primarily to monetize. Implications:

- **Parsers are community-contributed.** Anyone should be able to add their bank by editing data files and fixtures, without touching engine code. Optimize every change for that contributor experience.
- **Email ingestion is via forwarding rules, not the Gmail API.** Users add a Gmail forwarding rule (or any provider's equivalent) pointing to their per-user ingest address; a Cloudflare Email Routing worker POSTs the raw MIME to `POST /ingest/email`. The old Gmail-API polling path (Celery `src/tasks/email_fetch.py`, `EmailManager` in `src/email_service/manager.py`) is legacy, gated behind `GMAIL_POLLING_ENABLED=false`, and slated for removal.
- **Google OAuth is login-only** (`openid` + `userinfo.email` scopes, `src/oauth_service/google_oauth.py`). Never reintroduce Gmail scopes.
- **Worldwide, not Chile-only.** Hardcoded Chilean assumptions (CLP defaults, `America/Santiago`, Spanish-only labels, Chilean merchant keywords) are legacy to be generalized, not patterns to extend.
- A hosted cloud offering for non-technical users may exist later, but the repo is the OSS product; keep private-deployment specifics (the VPS, GHCR namespace, `finitum.app` domains) out of contributor-facing docs and templated in infra configs.
- **Planned: outbound webhooks.** Devs should be able to subscribe to events (new transaction parsed, transfer detected, etc.) and trigger their own automations from the data. Not implemented yet; design APIs with this event surface in mind.

The reference deployment is live at https://finitum.app (Lightsail VPS, deployed via the CI pipeline). Richard dogfoods it daily -- treat `main` as production.

## Architecture

- **Backend**: FastAPI (`src/api/server.py`), PostgreSQL + Alembic (`src/db/`, `alembic/`), Redis (dedupe + Gmail-confirmation capture).
- **Ingestion**: `src/email_service/ingest.py` -- resolves user by `ingest_token` from the `u-<token>@<INGEST_DOMAIN>` recipient, HMAC-verifies `X-Finitum-Signature` (`INGEST_WEBHOOK_SECRET`), dedupes on `Message-ID`, auto-captures Gmail forwarding-confirmation links/codes into Redis for one-click setup. Worker lives in `infra/email-worker/`.
- **Parsers**: fully data-driven. All bank logic lives in `src/parsers/regex.json` (per-bank: `remitents` sender allowlist, `subject` classification patterns, `body` extraction regexes). Engine: `src/parsers/parser.py` (`EmailParser`, `BankPatterns.from_json`). The bank is a per-user setting (`User.bank`); there is no content-based bank auto-detection. `GET /banks` derives the bank list from `regex.json` keys.
- **Categories**: keyword matching in `src/parsers/base.py` from root `categories.json`; slugs/labels registry in `src/category_catalog.py`; Spanish overrides in `category_labels.es.json`; per-user custom categories via `POST /categories` + `src/db/categories.py`.
- **Frontend**: React Router v7 + TypeScript + Tailwind + Bun in `web/` (file routes under `web/app/routes/`). `profile.tsx` holds the up-to-date forwarding-setup UX; `home.tsx` and `guide.tsx` still carry stale OAuth-era messaging.

## Adding a bank (the core contributor flow)

1. Add a bank block to `src/parsers/regex.json` (all body regex keys are required by `BankPatterns.from_json` validation).
2. Add sanitized sample fixtures under `tests/banks/<bank>/` (plain text body/subject files, e.g. `purchase_clp.txt`, `purchase_subject.txt`).
3. Add parametrized cases in `tests/test_parse.py`. Tests build `Message(...)` by hand and run `EmailParser(bank)` directly -- no network or Gmail needed.

## Conventions

- Python managed with `uv` (`uv.lock`, `uv sync --frozen`); lint with `ruff`; tests with `pytest`. CI in `.github/workflows/ci.yml` runs lint + tests on PRs.
- Run everything via Docker Compose (`docker compose up --build`); API on 9090.
- Write tests for behavior changes, especially parser changes (fixture-driven).
- English is the canonical language for docs, code, and labels; other locales are overrides.

## Known drift (do not trust these blindly)

- Root `README.md` still describes the OAuth/Gmail-API model and private EC2/GHCR deploy; `web/README.md` describes a layout that no longer exists; `terms/` texts assume the Gmail-access SaaS. The roadmap lives in `plans/` (phases 1-3) and `todo.md` -- `plans/phase-3-open-source-i18n.md` is the source of truth for the OSS/i18n work (LICENSE decision, CONTRIBUTING, docs/, issue templates, SECURITY.md are still missing).
