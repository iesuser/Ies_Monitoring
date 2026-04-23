from datetime import datetime, timezone

from src.extensions import db
from src.models.base import BaseModel


class ShakemapJob(db.Model, BaseModel):
    __tablename__ = "shakemap_jobs"

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_GENERATED = "generated"
    STATUS_FAILED = "failed"

    id = db.Column(db.Integer, primary_key=True)
    celery_task_id = db.Column(db.String(128), nullable=True, unique=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    seiscomp_oid = db.Column(db.String(20),db.ForeignKey("seismic_events.seiscomp_oid"),nullable=False,unique=True,index=True)
    seismic_event = db.relationship("SeismicEvent",back_populates="shakemap_job",uselist=False,foreign_keys=[seiscomp_oid])

    uuid = db.Column(db.String(255), db.ForeignKey('users.uuid'), nullable=False)
    user = db.relationship('User', back_populates='shakemap_jobs', foreign_keys=[uuid])

