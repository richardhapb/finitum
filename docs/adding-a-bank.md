# Adding a bank

Bank parsers in Finitum are **data-driven**: every bank is a JSON block in [`src/parsers/regex.json`](../src/parsers/regex.json), interpreted by the shared engine in [`src/parsers/parser.py`](../src/parsers/parser.py). Adding a bank requires no engine code -- just regexes and test fixtures. The API (`GET /banks`) and the web UI discover new banks automatically from `regex.json`.

## 1. Collect sample emails

Get raw samples of your bank's notification emails for each type Finitum understands:

- **Purchase** (card payment)
- **Withdrawal** (ATM)
- **Transference** (money transfer)

In Gmail use "Show Original" to see the actual source, including encoding artifacts. The parser receives the body after HTML stripping, so to see exactly what your regexes will run against, strip it the same way:

```python
from bs4 import BeautifulSoup

def remove_html_tags(html_doc: str) -> str:
    soup = BeautifulSoup(html_doc, "html.parser")
    return soup.get_text()
```

**Sanitize your samples before committing them**: replace real names, account numbers, national ids, and card digits with fake values that keep the same shape (same length/format), so the regexes still match.

## 2. Create test fixtures

Create a directory under `tests/banks/` for your bank:

```bash
mkdir -p tests/banks/your_bank_name
```

Add plain-text files per transaction type (body + subject):

- `purchase_clp.txt` / `purchase_subject.txt`
- `withdrawal.txt` / `withdrawal_subject.txt`
- `transference.txt` / `transference_subject.txt`

(The `_clp` suffix is historical -- use it for your local-currency purchase sample. Look at `tests/banks/banco_chile/` for a complete example.)

## 3. Write the patterns

Add your bank to `src/parsers/regex.json`:

```json
{
  "your_bank_name": {
    "remitents": ["notifications@yourbank.com"],
    "subject": {
      "exclusions": ["between my accounts"],
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
      "transferenceRecipient": "Recipient:\\s+(.+?)\\s+Account",
      "transferenceMatches": ""
    }
  }
}
```

Field reference:

| Field | Meaning |
|-------|---------|
| `remitents` | Sender addresses your bank uses. Emails from other senders are ignored, and the web UI builds the Gmail forwarding filter (`from:(...)`) from this list. |
| `subject.purchase` / `withdrawal` / `transference` | Lowercase regex fragments matched against the subject to classify the email. |
| `subject.exclusions` | Subjects to skip entirely (e.g. transfers between your own accounts). |
| `body.amount*` | Regex with one capture group extracting the amount for each type. |
| `body.commerce` | Capture group for the merchant name (purchases). |
| `body.date` | Regex matching the transaction date inside the body. |
| `body.transferenceRecipient` | Capture group for the transfer recipient's name. |
| `body.transferenceMatches` | Extra pattern a transfer body must contain (use `""` if not needed). |

All `body` keys are required -- `BankPatterns.from_json` validates them and raises if one is missing. Use `""` for patterns your bank doesn't need.

Pattern tips:

- Use `\\s+` for flexible whitespace; capture groups `(...)` extract the value.
- Emails often carry quoted-printable artifacts (`=C3=B1` for `ñ`, `=09` for tabs) and odd spacing left over from HTML stripping -- look at the fixture with `repr()` to see the exact characters.
- Amounts may use `.` or `,` as thousands separators depending on locale.
- Test candidate regexes at [regex101.com](https://regex101.com) against your fixture content.

## 4. Write tests

Add your bank to the parametrized cases in [`tests/test_parse.py`](../tests/test_parse.py):

```python
@pytest.mark.parametrize(
    ("bank", "amount", "commerce", "cat", "test_remitent"),
    [
        ("banco_chile", 38844, "STA ISABEL JM CAR", ExpenseCategory.FOOD, banco_chile_remitent),
        ("santander", 68885, "Entel pcs", ExpenseCategory.SERVICES, santander_remitent),
        ("your_bank_name", 15000, "COFFEE SHOP", ExpenseCategory.FOOD, "notifications@yourbank.com"),
    ],
)
```

Then run:

```bash
pytest tests/test_parse.py -v
```

Tests build a `Message` directly from your fixture files and run the parser -- no network, no email account, no running services needed. Add equivalent cases for withdrawals and transfers.

## 5. Debug failed matches

Dump the exact string being parsed and compare it character by character against your regex:

```python
with open("tests/banks/your_bank_name/purchase_clp.txt", encoding="utf-8") as f:
    print(repr(f.read()))  # shows exact bytes, whitespace, encoding
```

There is also a small CLI to run the parser against a raw email file without the test suite (run from the `src/` directory):

```bash
cd src
uv run python -m parsers.test_parse your_bank_name path/to/email.txt --raw
```

Common issues:

- **Commerce not captured**: adjust for the exact separators around the merchant name.
- **Wrong amount**: check thousands separators and whether the email contains multiple amounts (billed vs. paid).
- **Date mismatch**: `DD/MM/YYYY` vs `DD-MM-YYYY`, optional time component.
- **Nothing classified**: the subject patterns are matched lowercase -- check `subject.*` against the actual subject fixture.

## Categories

Merchant names are matched against keyword lists to auto-assign a category:

- Keywords live in [`categories.json`](../categories.json) (repo root), keyed by parser category.
- The category registry (slugs, English/Spanish labels) is in [`src/category_catalog.py`](../src/category_catalog.py); Spanish label overrides live in [`category_labels.es.json`](../category_labels.es.json).
- The closed set of built-in categories is the `ExpenseCategory` enum in [`src/parsers/base.py`](../src/parsers/base.py).

To improve detection for your bank's merchants, add keywords to `categories.json`. Matching is case-insensitive and accent-normalized, longest match first; unmatched merchants fall back to `GENERAL`. (Users can also define custom categories at runtime, so built-in keywords only need to cover the common cases.)

## Submitting your parser

Open a PR with the `regex.json` block, the sanitized fixtures, and the test cases. If you can't finish the parser yourself, open an [Add a bank issue](https://github.com/richardhapb/finitum/issues/new?template=add-a-bank.yml) with sanitized samples and someone can pick it up.
