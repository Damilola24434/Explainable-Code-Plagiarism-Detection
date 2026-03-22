import os

from celery import Celery

# Use in-memory broker for local development (no Redis needed).
# Set USE_REDIS=1 to enable Redis if available.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BROKER = REDIS_URL if os.getenv("USE_REDIS", "0") == "1" else "memory://"
BACKEND = REDIS_URL if os.getenv("USE_REDIS", "0") == "1" else "cache+memory://"

celery_app = Celery(
    "plagiarism_jobs",
    broker=BROKER,
    backend=BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
