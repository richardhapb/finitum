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

## Extending Finitum

### Adding Support for a New Bank

Finitum uses regex patterns to parse bank notification emails. Each bank has its own patterns defined in `src/parsers/regex.json`.

#### 1. Collect Sample Emails

Get raw email samples from your bank for:
- Purchase notifications
- ATM withdrawals
- Transfer notifications

Use "Show Original" in Gmail to get the actual email source, including encoding artifacts. Clean the text—the parser needs to handle the clean format.

Use this function to clean the html from email text.

```python
from bs4 import BeautifulSoup
def remove_html_tags(html_doc: str) -> str:
    soup = BeautifulSoup(html_doc, "html.parser")
    return soup.get_text()
```


#### 2. Create Test Files

Create a directory under `tests/banks/` for your bank:

```bash
mkdir -p tests/banks/your_bank_name
```

Add test files for each transaction type:
- `purchase_clp.txt` - Purchase notification body
- `purchase_subject.txt` - Purchase email subject
- `withdrawal.txt` - ATM withdrawal body
- `withdrawal_subject.txt` - ATM withdrawal subject
- `transference.txt` - Transfer notification body
- `transference_subject.txt` - Transfer email subject

#### 3. Write Regex Patterns

Add your bank's patterns to `src/parsers/regex.json`:

```json
{
  "your_bank_name": {
    "subject": {
      "exclusions": ["internal transfer", "between accounts"],
      "purchase": "purchase confirmation",
      "withdrawal": "atm withdrawal",
      "transference": "transfer notification"
    },
    "body": {
      "amountPurchase": "Amount\\s+\\$([\\d.,]+)",
      "amountTransference": "Transfer\\s+amount\\s+\\$([\\d.,]+)",
      "amountWithdrawal": "Withdrawal\\s+\\$([\\d.,]+)",
      "date": "\\d{1,2}[-/]\\d{1,2}[-/]\\d{4}",
      "commerce": "Merchant:\\s+(.+?)\\s+Date",
      "transferenceRecipient": "Recipient:\\s+(.+?)\\s+Account"
    }
  }
}
```

**Pattern Guidelines**:
- **Subject patterns**: Lowercase text fragments to match in email subjects
- **Exclusions**: Subject patterns to ignore (e.g., internal transfers)
- **Body patterns**: Regex to capture specific fields from email body
- Use `\\s+` for flexible whitespace matching
- Capture groups `(...)` extract the actual value
- Handle encoded characters if present (e.g., `=C3=B1` for `ñ`)
- Account for separators like `>`, tabs (`=09`), or HTML artifacts

**Common Pitfalls**:
- Emails often have quoted-printable encoding (`=C3=A9` for accented chars)
- HTML emails get stripped but may have odd spacing artifacts
- Line breaks might be `> ` or `\n` depending on email format
- Currency amounts may use `.` or `,` as thousands separators

#### 4. Write Tests

Add parametrized test cases in `tests/test_parse.py`:

```python
@pytest.mark.parametrize(
    ("bank", "amount", "commerce", "cat"),
    [
        ("banco_chile", 38844, "STA ISABEL JM CAR", ExpenseCategory.FOOD),
        ("santander", 68885, "Entel pcs", ExpenseCategory.SERVICES),
        ("your_bank_name", 15000, "COFFEE SHOP", ExpenseCategory.FOOD),
    ],
)
def test_amount_data_clp(bank, amount, commerce, cat):
    # Test implementation
    ...
```

#### 5. Run Tests

```bash
pytest tests/test_parse.py -v
```

Fix regex patterns until all tests pass. Common issues:
- **Commerce not captured**: Adjust the pattern to match the exact structure
- **Amount wrong format**: Handle thousands separators (`.` vs `,`)
- **Date format mismatch**: Update date regex for DD/MM/YYYY vs DD-MM-YYYY
- **Recipient name issues**: Account for ALL CAPS vs Mixed Case

#### 6. Debug Failed Matches

If regex doesn't match, dump the actual string being parsed:

```python
with open(f"tests/banks/{bank}/purchase_clp.txt", "r") as f:
    content = f.read()
    print(repr(content))  # Shows exact bytes, whitespace, encoding
```

Compare the `repr()` output against your regex pattern character by character.

### Adding New Transaction Categories

Categories are defined in `src/parsers/categories.json` and mapped in `src/parsers/base.py`.

#### 1. Edit Category Keywords

Add or modify categories in `src/parsers/categories.json`:

```json
{
  "food": ["grocery", "restaurant", "cafe", "market"],
  "transport": ["uber", "taxi", "metro", "gas station"],
  "your_new_category": ["keyword1", "keyword2", "keyword3"]
}
```

#### 2. Update ExpenseCategory Enum

Add your category to `src/parsers/base.py`:

```python
class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    YOUR_NEW_CATEGORY = "your_new_category"
```

#### 3. Test Category Detection

Categories are detected by matching merchant names against keywords. Test with:

```python
from parsers.expense import Expense

expense = Expense("100", "COFFEE SHOP", datetime.now())
assert expense.category == ExpenseCategory.FOOD
```

### Debugging Email Parsing Issues

Common problems and solutions:

**Emails not being fetched**:
- Check Celery logs: `docker compose logs celery_worker`
- Verify Gmail API scope includes read access
- Check Google OAuth token hasn't expired

**Regex not matching**:
- Email body might have HTML artifacts—check `remove_html_tags()` function
- Use `repr()` to see exact string format including hidden characters
- Test regex patterns at [regex101.com](https://regex101.com)

**Wrong amounts extracted**:
- Check for multiple amounts in email (bill amount vs. paid amount)
- Verify thousands separator handling (`.` vs `,`)
- Some banks show amounts in multiple places—ensure you're capturing the right one

**Categories wrong**:
- Add more specific keywords to `categories.json`
- Keywords are matched case-insensitive and after normalization
- Check keyword priority—more specific terms should come first

### Development Workflow

1. **Get raw email sample** (Show Original in Gmail)
2. **Create test files** with exact email content
3. **Write regex patterns** in `regex.json`
4. **Run tests** and iterate on patterns
5. **Debug with `repr()`** to see exact format
6. **Validate in production** with small date range first

### Performance Considerations

- Celery tasks fetch emails in batches (configurable in `tasks/email.py`)
- Rate limits apply to Gmail API (quota: 1 billion requests/day)
- Database queries are optimized with proper indexes
- Dashboard caches data for 5 minutes to reduce DB load

---

## Security

- No email content is saved—only extracted transaction data
- All sensitive tokens and credentials are stored securely in the database
- OAuth2 state is managed with Redis for CSRF protection
- Passwords are hashed using strong algorithms
- JWT tokens are used for authentication

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
