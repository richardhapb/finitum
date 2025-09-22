from celery import Celery
from kombu import Queue, Exchange
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
APP_NAME = "finitum"

celery = Celery(
    APP_NAME,
    broker=os.getenv("CELERY_BROKER_URL", REDIS_URL),
    backend=os.getenv("CELERY_RESULT_BACKEND", REDIS_URL),
    include=[
        "celery_service.tasks_parse",
    ],
)

# Queues: separate CPU/latency profiles
default_ex = Exchange(APP_NAME, type="direct")
celery.conf.task_queues = (
    Queue("parse", default_ex, routing_key="parse"),
)
celery.conf.task_default_queue = "parse"
celery.conf.task_default_exchange = APP_NAME
celery.conf.task_default_routing_key = "parse"

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
    task_time_limit=60 * 5,  # hard kill runaway tasks (5 min)
    task_soft_time_limit=60 * 4,  # soft timeout for cleanup
    result_expires=60 * 60,  # 1h
    enable_utc=True,
    timezone=os.getenv("TZ", "America/Santiago"),
)
