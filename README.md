# Finitum – Personal Finance Manager

Finitum is a modern, extensible personal finance manager that automatically parses your bank and email notifications to track expenses, transfers, and financial activity. It features a web dashboard, category detection, and secure OAuth integration with Google.

---

## Features

- **Automatic Email Parsing**: Connect your Gmail account and Finitum will extract expenses and transfers from bank notifications.
- **Category Detection**: Uses robust keyword matching and normalization to classify transactions into categories (Food, Transport, Online, etc.).
- **Dashboard**: Interactive Dash/Plotly dashboard for visualizing spending trends, top merchants, category breakdowns, and more.
- **User Authentication**: Secure signup/signin with JWT-based authentication.
- **Google OAuth2 Integration**: Securely authorize Gmail access using OAuth2.
- **Celery Task Queue**: Asynchronous background tasks for fetching and parsing emails.
- **PostgreSQL Database**: Stores users, transactions, and credentials securely.
- **Extensible**: Modular parser and category system for easy adaptation to new banks or notification formats.

---

## Quickstart (Docker Compose)

**The recommended way to run Finitum is via Docker Compose.**
No local Python or database setup required.

### 1. Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```env
CONN_STR=postgresql+psycopg://finitum:yourpassword@db:5432/finitum
PGUSER=finitum
PGPASSWORD=yourpassword
PGDATABASE=finitum
REDIS_URL=redis://redis:6379/0
GOOGLE_CLIENT=your-google-client-id
GOOGLE_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:9090/google_oauth2callback
SECRET_KEY=your-jwt-secret
TZ=America/Santiago
DEBUG=true
```

- You must create Google OAuth credentials for Gmail API access:
  [Google Cloud Console – Credentials](https://console.cloud.google.com/apis/credentials)

### 3. Build and Start All Services

```bash
docker compose up --build
```

This will start:

- **API server** (FastAPI, port 9090)
- **Dashboard** (Dash/Plotly, port 5050)
- **Celery worker** (background email parsing)
- **Celery beat** (periodic tasks)
- **PostgreSQL** (database, port 5444)
- **Redis** (cache, port 6379)
- **Alembic** (runs DB migrations on first up)

### 4. Access the App

- **Web Dashboard & API**: [http://localhost:9090](http://localhost:9090)
- **API Docs**: [http://localhost:9090/docs](http://localhost:9090/docs)

---

## Usage

1. **Sign Up**: Register a user via `/signup` endpoint or UI.
2. **Google OAuth**: Visit `/google-authorize` to link your Gmail account.
3. **Fetch Emails**: Celery tasks will periodically fetch and parse new emails.
4. **Dashboard**: Open the dashboard at [http://localhost:5050](http://localhost:5050) to view your financial analytics.

---

## Project Structure

```
src/
  api/              # FastAPI server, JWT auth, endpoints
  db/               # SQLModel models, DB service
  email_service/    # Gmail API integration, message parsing
  oauth_service/    # Google OAuth2 logic
  parsers/          # Expense/transference parsing, category logic
  tasks/            # Celery tasks for background processing
  ui/               # Dash/Plotly dashboard
  utils/            # Config, logging, helpers
alembic/            # Database migrations
tests/              # Unit and integration tests
```

---

## Security

- No email is saved.
- All sensitive tokens and credentials are stored securely in the database.
- OAuth2 state is managed with Redis for CSRF protection.
- Passwords are hashed using strong algorithms.
- JWT tokens are used for authentication.

---

## Extending

- **New Banks**: Add new parser classes in `src/parsers/`.
- **Categories**: Edit `categories.json` and `src/parsers/base.py` for new categories/keywords.
- **UI**: Extend the Dash dashboard in `src/ui/dashboard.py`.

---

## License

MIT License

---

## Acknowledgements

- [Dash](https://plotly.com/dash/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

