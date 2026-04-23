from celery import Celery
import os

celery = Celery(
    "shakemap",
    broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)

celery.conf.update(
    task_track_started=True,
    worker_concurrency=2,  # მაქსიმუმ 2 job ერთდროულად
    task_time_limit=600,  # hard timeout: 10 წუთი
    task_soft_time_limit=540,  # soft timeout: 9 წუთი
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=200000,  # KB (~200MB)
)

celery.autodiscover_tasks(["src.tasks"])