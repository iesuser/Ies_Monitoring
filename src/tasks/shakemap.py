# src/tasks/shakemap.py

from src.celery_app import celery
import os
from redis import Redis
from datetime import datetime, timezone
from src.extensions import db
from src.models import ShakemapJob
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker

@celery.task(bind=True)
def run_shakemap(self, job_id, requester_lock_key=None, lock_value=None):
    from src import create_app

    app = create_app()
    redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"), decode_responses=True)

    with app.app_context():
        job = db.session.get(ShakemapJob, job_id)
        if not job:
            return

        event = SeismicEvent.query.filter_by(seiscomp_oid=job.seiscomp_oid).first()

        try:
            job.status = ShakemapJob.STATUS_RUNNING
            job.started_at = datetime.now(timezone.utc)
            db.session.commit()

            if not event:
                raise ValueError(f"მოვლენა ვერ მოიძებნა: {job.seiscomp_oid}")

            parsed_data = {
                "event_id": event.event_id,
                "time": event.origin_time.isoformat(),
                "longitude": event.longitude,
                "latitude": event.latitude,
                "depth": event.depth,
                "ml": event.ml,
                "desc": event.region_ge or "მოვლენის აღწერა",
            }
            run_shakemap_worker(parsed_data)

            job.status = ShakemapJob.STATUS_GENERATED
            job.error = None
        except Exception as e:
            job.status = ShakemapJob.STATUS_FAILED
            job.error = str(e)
        finally:
            job.finished_at = datetime.now(timezone.utc)
            db.session.commit()

            if requester_lock_key and lock_value:
                try:
                    current_value = redis_client.get(requester_lock_key)
                    if current_value == lock_value:
                        redis_client.delete(requester_lock_key)
                except Exception:
                    pass