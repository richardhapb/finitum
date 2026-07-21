# Finitum

**Turn your bank's notification emails into structured financial data -- automatically.**

Finitum is an open-source personal finance tracker. Instead of scraping your bank or asking for your credentials, it uses the emails your bank already sends you: you set up a one-time forwarding rule, and every purchase, withdrawal, and transfer notification is parsed into a transaction (amount, merchant, date, category) and shown on your dashboard.

- **No inbox access.** Finitum never reads your email account. You forward only the bank notifications you choose; Google sign-in is optional and used for login only.
- **Community bank parsers.** Every bank's email format is described in a single JSON file -- no engine code needed. Adding your bank is a JSON block plus a couple of test fixtures. See [Adding a bank](docs/adding-a-bank.md).
- **Self-hostable.** One `docker compose up` runs the whole stack. A hosted instance lives at [finitum.app](https://finitum.app).
- **Privacy first.** Raw email content is processed in real time and never stored -- only the extracted transaction data.

License: [MIT](LICENSE).

## How it works

```
Your bank ──notification──▶ Your inbox ──forwarding rule──▶ u-<token>@your-domain
                                                                    │
                                                       Cloudflare Email Routing worker
                                                                    │ (HMAC-signed POST)
                                                                    ▼
                                                          Finitum API /ingest/email
                                                                    │
                                                        bank parser (regex.json)
                                                                    │
                                                                    ▼
                                                  transaction ──▶ dashboard 📊
```

1. Each user gets a unique ingest address (`u-<token>@<your-ingest-domain>`).
2. In Gmail (or any provider), you add that address as a forwarding target and create a filter for your bank's sender addresses. Finitum even captures Gmail's forwarding-confirmation email automatically so setup is one click.
3. Incoming mail is relayed by a small [Cloudflare Email Routing worker](infra/email-worker/) to the API, verified with an HMAC signature, deduplicated, parsed, and saved.

## Supported banks

| Bank | Country | Parser id |
|------|---------|-----------|
| Banco de Chile | 🇨🇱 Chile | `banco_chile` |
| Santander | 🇨🇱 Chile | `santander` |

Your bank not here? **You can add it without writing engine code** -- parsers are data-driven regex definitions with fixture-based tests. Follow [docs/adding-a-bank.md](docs/adding-a-bank.md) and open a PR, or open an [Add a bank](https://github.com/richardhapb/finitum/issues/new?template=add-a-bank.yml) issue with sanitized samples.

## Quickstart (self-host)

Requirements: [Docker + Docker Compose](https://docs.docker.com/get-docker/).

```bash
git clone https://github.com/richardhapb/finitum.git
cd finitum
cp .env.example .env   # fill in the values
docker compose up --build
```

This starts the FastAPI server (port 9090), the web app, PostgreSQL, Redis, and background workers; database migrations run automatically on first start.

- **App / API**: http://localhost:9090 (interactive API docs at `/docs`)

Key environment variables (see `.env.example` for the full list):

| Variable | Purpose |
|----------|---------|
| `CONN_STR`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | PostgreSQL connection |
| `REDIS_URL` | Redis (dedupe, forwarding-confirmation capture) |
| `SECRET_KEY` | JWT signing secret |
| `INGEST_WEBHOOK_SECRET` | Shared secret between the email worker and the API |
| `INGEST_DOMAIN` | Domain of the per-user ingest addresses |
| `GOOGLE_CLIENT`, `GOOGLE_SECRET`, `GOOGLE_REDIRECT_URI` | Optional -- Google sign-in (login only, no Gmail scopes) |
| `TZ` | Timezone for parsed email dates |

To receive real emails you also deploy the email worker on your own domain -- see [infra/email-worker/](infra/email-worker/) for a 5-minute setup with Cloudflare Email Routing.

## Adding your bank in 3 steps

1. **Describe the emails**: add a block for your bank to [`src/parsers/regex.json`](src/parsers/regex.json) -- sender addresses, subject patterns per transaction type, and body regexes that capture amount, merchant, and date.
2. **Add fixtures**: drop sanitized sample email bodies/subjects into `tests/banks/<your_bank>/`.
3. **Add a test case**: extend the parametrized cases in [`tests/test_parse.py`](tests/test_parse.py) and run `pytest tests/test_parse.py -v`.

That's it -- the API and the web UI pick up new banks automatically from `regex.json`. The full guide, including regex tips, encoding pitfalls, and a CLI for testing against a raw email file, is in [docs/adding-a-bank.md](docs/adding-a-bank.md).

## Project structure

```
src/
  api/              # FastAPI server, JWT auth, ingest webhook, endpoints
  db/               # SQLModel models, DB services
  email_service/    # Inbound email processing (MIME parsing, ingest pipeline)
  oauth_service/    # Google sign-in (login only)
  parsers/          # Bank parsers engine + regex.json definitions
  utils/            # Config, logging, helpers
web/                # React Router v7 + Tailwind frontend
infra/email-worker/ # Cloudflare Email Routing worker (forwarding relay)
alembic/            # Database migrations
tests/              # Test suite + sample bank emails (tests/banks/)
docs/               # Contributor and operator documentation
```

## Roadmap

- **Outbound webhooks**: subscribe to events (`transaction.created`, transfers, ...) and trigger your own automations.
- **Internationalization**: English-canonical labels with per-locale overrides; per-user timezone and currency handling.
- **Multi-bank per user** with sender-based parser dispatch.

See [plans/](plans/) for the detailed phase documents.

## Contributing

Contributions are very welcome -- bank parsers most of all. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Please also read the [Code of Conduct](CODE_OF_CONDUCT.md). Security issues: see [SECURITY.md](SECURITY.md).

Deployment/CI notes for operators of the reference instance are in [docs/deployment.md](docs/deployment.md).

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [React Router](https://reactrouter.com/)
- [Cloudflare Email Routing](https://developers.cloudflare.com/email-routing/)
