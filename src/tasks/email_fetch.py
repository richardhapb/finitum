from datetime import UTC, datetime, timedelta

from google.auth.exceptions import RefreshError
import sqlmodel
import db.models as md

from db.service import get_session
from email_service.manager import EmailManager, Message, normalize_date_from
from parsers.parser import BankNotFoundError, EmailParser, save_expense
from tasks.app import celery
from utils.config import TZ
from utils.logger import get_logger

logger = get_logger()


@celery.task(
    bind=False,
    autoretry_for=(Exception,),
    dont_autoretry_for=(RefreshError,),  # Token expired/revoked - not retryable
    retry_backoff=True,  # exponential (1, 2, 4, 8…)
    retry_backoff_max=300,  # cap at 5 minimum
    retry_jitter=True,
    max_retries=5,
    default_retry_delay=5,
    queue="parse",
    routing_key="parse",
)
def get_user_messages(user_id: int) -> None:
    logger.info("Retrieving messages for user %d", user_id)

    with next(get_session()) as session:
        user_query = sqlmodel.select(md.User).where(md.User.id == user_id)
        user = session.exec(user_query).one()

        credentials_query = sqlmodel.select(md.UserGoogleCredential).where(md.UserGoogleCredential.user == user)
        credentials_obj = session.exec(credentials_query).one() if user else None

        if not credentials_obj:
            logger.error(
                "Missed user/credentials, user=%s, credentials=%s",
                user.username if user else None,
                credentials_obj,
            )
            return

        # Skip users with invalid (expired/revoked) credentials
        if not credentials_obj.is_valid:
            logger.warning("Skipping user %s: credentials marked as invalid", user.username)
            return

        credentials = md.rebuild_credentials(credentials_obj)

        parser = EmailParser(user.bank, user.email)
        try:
            parser.build_parser()
        except BankNotFoundError:
            logger.exception("Cannot parse the bank: %s", user.bank)
            return

        em: EmailManager = EmailManager(credentials)

        now = datetime.now(TZ)
        last = normalize_date_from(user.last_update) or (now - timedelta(days=30))
        # Use second precision to avoid day-boundary/timezone mismatches.
        query = f"after:{int(last.astimezone(UTC).timestamp())}"

        user.last_update = now

        try:
            session.add(user)
            msgs = em.get_messages(query, date_from=last)
            logger.info("%d messages fetched successfully for user %s", len(msgs), user.username)
            saved_msgs = 0
            for m in msgs:
                saved = save_message(user_id, parser, m, session)
                if saved:
                    saved_msgs += 1
        except RefreshError:
            # Token expired/revoked - mark credentials as invalid
            logger.error("Google OAuth refresh failed for user %s; marking credentials as invalid", user.username)
            credentials_obj.is_valid = False
            session.add(credentials_obj)
            session.commit()
            return
        except Exception:
            logger.exception("Cannot save messages for user %d", user_id)
            session.rollback()
            raise
        else:
            session.commit()

        logger.info("%d expenses saved for user %s", saved_msgs, user.username)


@celery.task(
    bind=False,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    default_retry_delay=5,
    queue="periodic",
    routing_key="periodic",
)
def get_messages() -> None:
    # Only fetch users with valid Google credentials
    users_query = sqlmodel.select(md.User).join(md.UserGoogleCredential).where(md.UserGoogleCredential.is_valid)
    with next(get_session()) as session:
        users = session.exec(users_query).all()

        logger.info("Retrieving messages for %d users", len(users))

        for i, user in enumerate(users):
            get_user_messages.apply_async(
                args=[user.id],
                countdown=i * 2,  # Avoid Redis flood
            )


def save_message(user_id: int, parser: EmailParser, msg: Message, session: sqlmodel.Session) -> bool:
    result = save_expense(user_id, parser, msg, session)

    if not result:
        logger.debug("Email is not a expense")
        return False

    return True
