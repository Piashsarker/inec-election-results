"""Celery application configuration for INEC Election Results Agent.

This module configures the Celery application with Redis as the broker
and result backend, sets up task routing, and configures concurrency settings.

Requirements: 6.3, 6.4
"""

import logging
from typing import Any

from celery import Celery

from app.config import get_settings

logger = logging.getLogger("inec_agent.workers.celery_app")

# Get settings
settings = get_settings()

# Create Celery application
celery_app = Celery(
    "inec_election_agent",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after completion for reliability
    task_reject_on_worker_lost=True,  # Reject tasks if worker is lost
    task_track_started=True,  # Track when tasks start

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,  # Store additional task metadata

    # Worker settings
    worker_concurrency=settings.celery.worker_concurrency,
    worker_prefetch_multiplier=1,  # Fetch one task at a time for fair distribution
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks

    # Task routing
    task_default_queue=settings.celery.task_default_queue,
    task_queues={
        settings.celery.task_default_queue: {
            "exchange": settings.celery.task_default_queue,
            "routing_key": settings.celery.task_default_queue,
        },
        "scraping": {
            "exchange": "scraping",
            "routing_key": "scraping",
        },
        "export": {
            "exchange": "export",
            "routing_key": "export",
        },
    },
    task_routes={
        "app.workers.tasks.run_scraping_job": {"queue": "scraping"},
        "app.workers.tasks.generate_csv_export": {"queue": "export"},
        "app.workers.tasks.generate_json_export": {"queue": "export"},
    },

    # Beat scheduler settings (for periodic tasks if needed)
    beat_scheduler="celery.beat:PersistentScheduler",

    # Retry settings
    task_default_retry_delay=60,  # Default retry delay of 60 seconds
    task_max_retries=3,  # Default max retries

    # Soft and hard time limits
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=3900,  # 1 hour 5 minutes hard limit
)

# Task autodiscovery
celery_app.autodiscover_tasks(["app.workers"])


def get_celery_app() -> Celery:
    """Get the configured Celery application instance.

    Returns:
        Celery: The configured Celery application
    """
    return celery_app


def get_task_info(task_id: str) -> dict[str, Any]:
    """Get information about a Celery task.

    Args:
        task_id: The Celery task ID

    Returns:
        Dictionary containing task state and result information
    """
    result = celery_app.AsyncResult(task_id)

    info: dict[str, Any] = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }

    # Add result or error info if available
    if result.ready():
        if result.successful():
            info["result"] = result.result
        elif result.failed():
            info["error"] = str(result.result)
            info["traceback"] = result.traceback
    elif result.status == "PROGRESS":
        # Custom progress state
        info["progress"] = result.info

    return info


def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """Revoke (cancel) a Celery task.

    Args:
        task_id: The Celery task ID to revoke
        terminate: If True, terminate the task even if it's running

    Returns:
        True if revocation was sent successfully
    """
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        logger.info(f"Revoked task {task_id} (terminate={terminate})")
        return True
    except Exception as e:
        logger.error(f"Failed to revoke task {task_id}: {e}")
        return False


logger.info(
    f"Celery app configured with broker: {settings.get_celery_broker_url()}, "
    f"concurrency: {settings.celery.worker_concurrency}"
)
