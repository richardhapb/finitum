"""
Quick test script for email parsing without running the full project.

Usage:
    python -m parsers.test_parse <bank> <email_file>
    python -m parsers.test_parse banco_chile sample_email.txt

The email file should contain the raw base64url-encoded email (from Gmail API)
or you can use --raw flag for a raw .eml file.
"""

import argparse
import base64
import sys
from pathlib import Path

from email_service.manager import Message
from parsers.parser import EmailParser


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def parse(bank: str, email_path: str, raw: bool = False) -> None:
    path = Path(email_path)
    if not path.exists():
        print(f"File not found: {email_path}")
        sys.exit(1)

    content = path.read_bytes()

    if raw:
        # Convert raw .eml to base64url format (like Gmail API returns)
        email_b64 = b64url_encode(content)
    else:
        # Already base64url encoded
        email_b64 = content.decode("utf-8").strip()

    print(f"Parsing email with bank: {bank}")
    print("-" * 50)

    # Parse the message
    msg = Message.parse_message(email_b64)
    if not msg:
        print("Failed to parse message (filtered by date?)")
        return

    print(f"From: {msg.remitent}")
    print(f"Subject: {msg.subject}")
    print(f"Date: {msg.date}")
    print(f"Body length: {len(msg.body)} chars")
    print("-" * 50)
    print("Full body (for regex debugging):")
    print(repr(msg.body[:1500]))  # repr shows newlines as \n
    print("-" * 50)
    print("Body preview (readable):")
    print(msg.body[:800])
    print("-" * 50)

    # Try to classify and extract
    parser = EmailParser(bank)
    try:
        parser.build_parser()
    except Exception as e:
        print(f"Failed to build parser: {e}")
        return

    expense_type = parser._classify_message(msg)
    print(f"Classified as: {expense_type}")

    if not expense_type:
        print("Message not classified as expense/transference")
        return

    # Try to extract expense or transference
    from parsers.parser import ExpenseType

    if expense_type == ExpenseType.TRANSFERENCE:
        transf = parser.get_transference(msg)
        print(f"Transference: {transf}")
    else:
        expense = parser.get_expense(msg)
        print(f"Expense: {expense}")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Test email parsing")
    argparser.add_argument("bank", help="Bank name (e.g., banco_chile, santander)")
    argparser.add_argument("email_file", help="Path to email file")
    argparser.add_argument("--raw", action="store_true", help="Email file is raw .eml format")

    args = argparser.parse_args()
    parse(args.bank, args.email_file, args.raw)
