from datetime import datetime, timedelta

from sqlmodel import select

from email_service.manager import EmailManager, normalize_date_from
from tasks.app import celery
from utils.config import TZ
from utils.logger import get_logger

logger = get_logger()


@celery.task(
    bind=False,
    autoretry_for=(Exception,),
    retry_backoff=True,  # exponential (1, 2, 4, 8…)
    retry_backoff_max=300,  # cap at 5 minimum
    retry_jitter=True,
    max_retries=5,
    default_retry_delay=5,
    queue="parse",
    routing_key="parse",
)
def get_messages() -> None:
    from db.models import User, UserGoogleCredential, rebuild_credentials
    from db.service import get_session

    with next(get_session()) as session:
        user_query = select(User).where(User.username == "richardhapb")
        user = session.exec(user_query).one()

        credentials_query = select(UserGoogleCredential).where(UserGoogleCredential.user == user)
        credentials_obj = session.exec(credentials_query).one() if user else None

        if user and credentials_obj:
            credentials = rebuild_credentials(credentials_obj)
            em: EmailManager = EmailManager(user, credentials)

            last = normalize_date_from(user.last_update) or datetime.now(TZ)
            last = datetime.now() - timedelta(days=1)
            query = f"is:unread after:{last.strftime('%Y/%m/%d')}"

            msgs = em.get_messages(query, date_from=last)
            for m in msgs:
                print()
                print("=" * 80)
                print(m)
        else:
            from utils.logger import get_logger

            logger = get_logger()
            logger.error(
                "Missed user/credentials, user=%s, credentials=%s",
                user.username if user else None,
                credentials_obj,
            )
