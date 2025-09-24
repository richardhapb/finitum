from tasks.app import celery
from email_service.processor import process_new_messages
from db.models import User, UserGoogleCredential, rebuild_credentials
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
    from db.service import get_session
    with next(get_session()) as session:
        user = session.get(User, {"username": "richardhapb"})
        credentials_obj = session.get(UserGoogleCredential, {"user": user}) if user else None
        if user and credentials_obj:
            credentials = rebuild_credentials(credentials_obj)
            process_new_messages(user, credentials, "is:unread", session, user.last_update)
        else:
            logger.error("Missed user/credentials, user=%s, credentials=%s", user, credentials_obj)
