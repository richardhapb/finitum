from datetime import datetime
from google.oauth2.credentials import Credentials
from sqlmodel import Session
from db.service import get_session
from utils.logger import get_logger
from email_service.manager import EmailManager
from parsers.expense import save_extracted_expense
from parsers.transference import save_extracted_transference
from db.models import User, UserGoogleCredentials, rebuild_credentials

logger = get_logger()


def process_new_messages(
    user: User, credentials: Credentials, query: str, session: Session, date_from: datetime | None = None
):
    em: EmailManager = EmailManager(user, credentials)
    try:
        messages = em.get_messages(query, date_from)
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

        user.last_update = datetime.now()
        session.refresh(user)
        session.commit()
    except Exception as e:
        logger.error("Error processing messages: %s", e, exc_info=True)


if __name__ == "__main__":
    with next(get_session()) as session:
        user = session.get(User, {"username": "richardhapb"})
        credentials_obj = session.get(UserGoogleCredentials, {"user": user}) if user else None
        if user and credentials_obj:
            credentials = rebuild_credentials(credentials_obj)
            process_new_messages(user, credentials, "is:unread", session, user.last_update)
        else:
            logger.error("Missed user/credentials, user=%s, credentials=%s", user, credentials_obj)
