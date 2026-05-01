# src/tasks/shakemap.py

from datetime import datetime, timezone
import logging

from src.celery_app import celery
from src.models import ShakemapJob
from src.models.seismic_event import SeismicEvent
from src.workers.run_shakemap import run_shakemap_worker

logger = logging.getLogger("app.shakemap")


@celery.task(bind=True)
def run_shakemap(self, job_id):
    # app_context ავტომატურად ედება src/celery_app.py-ის FlaskTask wrapper-იდან.
    job = ShakemapJob.query.get(job_id)
    if not job:
        logger.warning("ShakeMap task skipped: job not found (job_id=%s)", job_id)
        return

    event_oid = job.seiscomp_oid
    event = SeismicEvent.query.filter_by(seiscomp_oid=event_oid).first()

    try:
        job.status = ShakemapJob.STATUS_RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.error = None
        job.save()

        if not event:
            raise ValueError(f"მოვლენა ვერ მოიძებნა: {event_oid}")

        parsed_data = {
            "seiscomp_oid": event.seiscomp_oid,
            "time": event.origin_time.isoformat(),
            "longitude": event.longitude,
            "latitude": event.latitude,
            "depth": event.depth,
            "ml": event.ml,
            "desc": event.region_ge or "მოვლენის აღწერა",
        }
        logger.info("ShakeMap worker started for event: %s", event_oid)
        run_shakemap_worker(parsed_data)

        job.status = ShakemapJob.STATUS_GENERATED
        job.error = None
        logger.info("ShakeMap worker finished for event: %s", event_oid)
    except Exception as e:
        job.status = ShakemapJob.STATUS_FAILED
        job.error = str(e)
        logger.exception("ShakeMap worker failed for event: %s", event_oid)
    finally:
        job.finished_at = datetime.now(timezone.utc)
        job.save()