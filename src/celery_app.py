from celery import Celery
import os

celery = Celery(
    "shakemap",
    broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)


class FlaskTask(celery.Task):
    """Celery task wrapper Flask app_context-ით (lazy init)."""

    _flask_app = None

    def __call__(self, *args, **kwargs):
        if self._flask_app is None:
            # Lazy import/init, რომ მოდულის ჩატვირთვისას არ გაჩნდეს ციკლური import.
            from src import create_app

            self._flask_app = create_app()
        with self._flask_app.app_context():
            return super().__call__(*args, **kwargs)


celery.Task = FlaskTask

celery.conf.update(
    task_track_started=True,
    worker_concurrency=1,  # რიგობრივად ერთი job ერთდროულად
    task_time_limit=600,  # hard timeout: 10 წუთი
    task_soft_time_limit=540,  # soft timeout: 9 წუთი
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=200000,  # KB (~200MB)
)

celery.autodiscover_tasks(["src.tasks"])

# Backward compatibility: systemd/conf-ში გამოყენებული სახელი.
celery_app = celery