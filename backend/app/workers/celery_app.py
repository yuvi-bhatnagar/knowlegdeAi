from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "knowledge_ai_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes maximum for heavy documents
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=False,
    broker_transport_options={"max_retries": 1, "socket_timeout": 1.0},
)
