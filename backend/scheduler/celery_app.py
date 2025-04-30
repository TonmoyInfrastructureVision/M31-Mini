import os
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, task_failure, task_success
import logging

from config.settings import settings
from config.logging_config import setup_logging

# Configure logging
logging_config = setup_logging()
logger = logging.getLogger(__name__)

# Configure Celery
app = Celery(
    "m31_mini",
    broker=settings.scheduler.broker_url,
    backend=settings.scheduler.result_backend,
    include=["scheduler.tasks"]
)

# Configure Celery settings
app.conf.update(
    task_serializer=settings.scheduler.task_serializer,
    accept_content=settings.scheduler.accept_content,
    result_serializer=settings.scheduler.result_serializer,
    enable_utc=settings.scheduler.enable_utc,
    worker_concurrency=settings.scheduler.worker_concurrency,
    task_time_limit=settings.scheduler.task_time_limit,
    task_soft_time_limit=settings.scheduler.task_soft_time_limit,
    worker_prefetch_multiplier=settings.scheduler.worker_prefetch_multiplier,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_disable_rate_limits=False,
    task_default_rate_limit="10/m",
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=5,
    result_expires=3600,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    broker_pool_limit=10,
    broker_transport_options={"visibility_timeout": 3600},
)

# Configure scheduled tasks if beat is enabled
if settings.scheduler.beat_enabled:
    app.conf.beat_schedule = {
        "cleanup-completed-tasks": {
            "task": "scheduler.tasks.cleanup_old_completed_tasks",
            "schedule": 3600.0,  # Run every hour
            "args": (7,),  # Keep completed tasks for 7 days
        },
        "retry-failed-tasks": {
            "task": "scheduler.tasks.retry_failed_tasks",
            "schedule": 300.0,  # Run every 5 minutes
            "args": (),
        },
        "process-scheduled-tasks": {
            "task": "scheduler.tasks.process_scheduled_tasks",
            "schedule": 60.0,  # Run every minute
            "args": (),
        },
        "health-check": {
            "task": "scheduler.tasks.health_check",
            "schedule": 300.0,  # Run every 5 minutes
            "args": (),
        },
    }


# Register signal handlers
@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    logger.info(f"Worker {sender.hostname} is ready")


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    logger.info(f"Worker {sender.hostname} is shutting down")


@task_failure.connect
def on_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    logger.error(f"Task {task_id} failed: {str(exception)}")


@task_success.connect
def on_task_success(sender, result, **kwargs):
    logger.debug(f"Task {sender.request.id} completed successfully")


# Export app instance
if __name__ == "__main__":
    app.start() 