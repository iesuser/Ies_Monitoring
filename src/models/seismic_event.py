from datetime import datetime, timezone
from src.extensions import db
from src.models.base import BaseModel

class SeismicEvent(db.Model, BaseModel):
    __tablename__ = "seismic_events"

    event_id = db.Column(db.Integer, primary_key=True)
    seiscomp_oid = db.Column(db.String(50))
    origin_time = db.Column(db.DateTime, nullable=False)
    origin_msec = db.Column(db.Integer)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=True)
    region_ge = db.Column(db.String(100))
    region_en = db.Column(db.String(100))
    area = db.Column(db.String(50))
    ml = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now())

    def __repr__(self):
        return f"<SeismicEvent id={self.event_id} lat={self.latitude} lon={self.longitude}>"