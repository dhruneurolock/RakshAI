"""Celery configuration"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "neuropent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.agents.recon",
        "app.agents.strategy",
        "app.agents.executor",
        "app.agents.poc_generator",
        "app.agents.validator",
        "app.agents.coordinator"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    "app.agents.recon.*": {"queue": "recon"},
    "app.agents.strategy.*": {"queue": "strategy"},
    "app.agents.executor.*": {"queue": "executor"},
    "app.agents.poc_generator.*": {"queue": "poc"},
    "app.agents.validator.*": {"queue": "validator"},
    "app.agents.coordinator.*": {"queue": "coordinator"},
}
