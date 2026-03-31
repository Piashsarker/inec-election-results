"""Celery workers and background tasks.

This module exports the Celery application and task functions for
background job processing.

Requirements: 6.3, 6.4, 8.1, 8.2
"""

from app.workers.celery_app import (
    celery_app,
    get_celery_app,
    get_task_info,
    revoke_task,
)
from app.workers.tasks import (
    cancel_scraping_job,
    generate_csv_export,
    generate_json_export,
    pause_scraping_job,
    resume_scraping_job,
    run_scraping_job,
)

__all__ = [
    # Celery app
    "celery_app",
    "get_celery_app",
    "get_task_info",
    "revoke_task",
    # Scraping tasks
    "run_scraping_job",
    "pause_scraping_job",
    "resume_scraping_job",
    "cancel_scraping_job",
    # Export tasks
    "generate_csv_export",
    "generate_json_export",
]
