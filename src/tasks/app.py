import os

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from utils.config import APP_NAME, REDIS_URL

celery = Celery(
    APP_NAME,
    broker=os.getenv("CELERY_BROKER_URL", REDIS_URL),
    backend=os.getenv("CELERY_RESULT_BACKEND", REDIS_URL),
    include=[
        "tasks.email",
    ],
)

# Queues: separate CPU/latency profiles
default_ex = Exchange(APP_NAME, type="direct")
celery.conf.task_queues = (
    Queue("parse", default_ex, routing_key="parse"),
    Queue("periodic", default_ex, routing_key="periodic"),
)
celery.conf.task_default_queue = "periodic"
celery.conf.task_default_exchange = APP_NAME
celery.conf.task_default_routing_key = "periodic"

# Reliability & perf
celery.conf.update(
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        # Prevent “ghost” tasks if a worker dies mid-task
        "visibility_timeout": 60 * 30,  # 30 min
    },
    task_acks_late=True,  # ack only after task completes
    task_reject_on_worker_lost=True,  # requeue on worker crash
    worker_prefetch_multiplier=1,  # avoid hogging tasks under load
    task_time_limit=60 * 10,  # hard kill runaway tasks (10 min)
    task_soft_time_limit=60 * 4,  # soft timeout for cleanup
    result_expires=60 * 60,  # 1h
    enable_utc=True,
    timezone=os.getenv("TZ", "America/Santiago"),
)

celery.conf.beat_schedule = {
    "fetch-all-users-messages": {
        "task": "tasks.email.get_messages",
        "schedule": crontab(minute=0, hour='8,20'),
        "options": {
            "queue": "periodic",
            "routing_key": "periodic",
        },
    },
}
