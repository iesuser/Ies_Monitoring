from datetime import datetime, timezone
from src.extensions import db
from src.models.base import BaseModel


class SeismicEvent(db.Model, BaseModel):
    __tablename__ = "seismic_events"

    event_id = db.Column(db.Integer, primary_key=True)
    seiscomp_oid = db.Column(db.String(20), nullable=False, unique=True, index=True)
    origin_time = db.Column(db.DateTime, nullable=False)
    origin_msec = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=True)
    region_ge = db.Column(db.String(100))
    region_en = db.Column(db.String(100))
    area = db.Column(db.String(20))
    ml = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # ShakeMap status იკითხება დაკავშირებული job-დან (ბმა seiscomp_oid-ით).
    shakemap_job = db.relationship(
        "ShakemapJob",
        back_populates="seismic_event",
        uselist=False,
    )

    @property
    def shakemap_status(self):
        """ShakeMap job-ის მიმდინარე სტატუსი (job არარსებობისას pending)."""
        if self.shakemap_job and self.shakemap_job.status:
            return self.shakemap_job.status
        return "pending"

    def __repr__(self):
        return f"<SeismicEvent id={self.event_id} lat={self.latitude} lon={self.longitude}>"