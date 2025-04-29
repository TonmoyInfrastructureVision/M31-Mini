from celery import Celery
from celery.signals import worker_ready, worker_shutdown

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


app = Celery(
    "m31_mini",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
)

app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=["json"],
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_hijack_root_logger=False,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Load tasks from the tasks module
app.autodiscover_tasks(["scheduler.tasks"], force=True)


@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("Celery worker is ready")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger.info("Celery worker is shutting down") 