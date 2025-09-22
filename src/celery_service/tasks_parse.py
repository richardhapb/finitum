from celery_service.app import celery
from datetime import datetime
from processor import process_new_messages
from database import create_db_and_tables, get_session


@celery.task(
    bind=False,
    autoretry_for=(Exception,),
    retry_backoff=True,  # exponential (1, 2, 4, 8…)
    retry_backoff_max=300,  # cap at 5 min
    retry_jitter=True,
    max_retries=5,
    default_retry_delay=5,
    queue="parse",
    routing_key="parse",
)
def parse_message() -> None:
    with next(get_session()) as session:
        create_db_and_tables()
        process_new_messages(session, datetime(year=2025, month=1, day=1))
