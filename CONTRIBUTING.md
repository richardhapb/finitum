# Contributing to Finitum

Thanks for your interest in Finitum! Contributions of all kinds are welcome, but the one we want most is simple: **add your bank**. Parsers are data-driven (JSON + regex + fixtures, no engine code), and every new bank makes Finitum useful to more people. The complete guide is [docs/adding-a-bank.md](docs/adding-a-bank.md).

## Ways to contribute

- **Add a bank parser** -- see [docs/adding-a-bank.md](docs/adding-a-bank.md). No Python required.
- **Improve category detection** -- add merchant keywords to `categories.json`.
- **Report bugs / propose features** -- use the [issue templates](https://github.com/richardhapb/finitum/issues/new/choose).
- **Improve the core** -- backend (FastAPI), frontend (React Router), the ingest pipeline, or the docs.

## Development setup

The backend uses Python 3.12+ managed with [uv](https://docs.astral.sh/uv/); the frontend uses [Bun](https://bun.sh/).

**Full stack via Docker (recommended for running the app):**

```bash
cp .env.example .env   # fill in the values
docker compose up --build
```

**Backend only (for tests and linting):**

```bash
uv sync
uv run pytest          # run the test suite
uv run ruff check      # lint
```

Parser tests need no services at all -- they run against text fixtures in `tests/banks/`:

```bash
uv run pytest tests/test_parse.py -v
```

**Frontend:**

```bash
cd web
bun install
bun run dev            # dev server
bun run typecheck      # typegen + tsc
bun run lint           # eslint
```

## Pull requests

- Branch from `main`; keep PRs focused on one change.
- **Include tests** for anything that changes behavior. For parsers this means fixtures + parametrized cases (see the guide); CI runs `ruff` and `pytest` on every PR.
- **Sanitize fixtures**: sample emails must not contain real names, account numbers, national ids, or card digits. Replace them with fake values of the same shape.
- Keep the parser engine generic -- bank-specific logic belongs in `regex.json`, not in Python.
- New user-facing text should be in English; localized labels are handled via the category catalog overrides.

## Questions

Open a [discussion or issue](https://github.com/richardhapb/finitum/issues), or email finitumapp@gmail.com. Security issues: please follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
