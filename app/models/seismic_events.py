from app.extensions import db
from app.models.base import BaseModel


class SeismicEvent(db.Model, BaseModel):
    __tablename__ = "seismic_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    iesdata_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    seiscomp_oid = db.Column(db.String(100), unique=True, nullable=True, index=True)

    origin_time = db.Column(db.DateTime, nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=True)

    location_ge = db.Column(db.String(500), nullable=True)
    location_en = db.Column(db.String(500), nullable=True)
    area = db.Column(db.String(255), nullable=True)
    is_automatic = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    event_magnitudes = db.relationship(
        "EventMagnitude",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="select",
    )
    beachball = db.relationship(
        "EventBeachball",
        back_populates="event",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="select",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "iesdata_id": self.iesdata_id,
            "seiscomp_oid": self.seiscomp_oid,
            "origin_time": self.origin_time.isoformat() if self.origin_time else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "depth": self.depth,
            "location_ge": self.location_ge,
            "location_en": self.location_en,
            "area": self.area,
            "is_automatic": bool(self.is_automatic),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "magnitudes": [item.to_dict() for item in self.event_magnitudes],
            "beachball": self.beachball.to_dict() if self.beachball else None,
        }

    def __repr__(self):
        return (
            f"<SeismicEvent id={self.id} origin_time={self.origin_time} "
            f"lat={self.latitude} lon={self.longitude}>"
        )
