from datetime import datetime
from sqlmodel import Session
from database import create_db_and_tables, get_session
from utils import get_logger
from email_manager import EmailManager
from parse import save_extracted_expense, save_extracted_transference

logger = get_logger()


def process_new_messages(session: Session, date_form: datetime | None = None):
    em: EmailManager = EmailManager()
    try:
        messages = em.get_messages(date_form)
        n = len(messages)
        for i, msg in enumerate(messages):
            logger.info("Inserting to database message %d of %d", i + 1, n)
            if "entre mis cuentas" in msg.subject.lower():
                logger.info("Skipping transference between owned accounts")
                continue
            if "transferencia" in msg.subject.lower():
                _ = save_extracted_transference(msg, session)
            else:
                _ = save_extracted_expense(msg, session)
    except Exception as e:
        logger.error("Error processing messages: %s", e, exc_info=True)


if __name__ == "__main__":
    with next(get_session()) as session:
        create_db_and_tables()
        process_new_messages(session, datetime(year=2025, month=1, day=1))
