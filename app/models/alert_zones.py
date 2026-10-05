from app.extensions import db
from app.models.base import BaseModel


class AlertZone(db.Model, BaseModel):
    __tablename__ = "alert_zones"

    NOTIF_CHANNELS = ("mail", "number", "push_notif")

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)

    # GeoJSON Polygon geometry: {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}
    geometry = db.Column(db.JSON, nullable=False)

    # ML (local magnitude) thresholds; None for max_magnitude means no upper limit
    min_magnitude = db.Column(db.Float, nullable=False)
    max_magnitude = db.Column(db.Float, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True, index=True)

    notif_is_staff = db.Column(db.Boolean, nullable=False, default=False)
    # Subset of NOTIF_CHANNELS, e.g. ["mail", "push_notif"]
    notif_channels = db.Column(db.JSON, nullable=False, default=list)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "geometry": self.geometry,
            "min_magnitude": self.min_magnitude,
            "max_magnitude": self.max_magnitude,
            "enabled": self.enabled,
            "notif_is_staff": self.notif_is_staff,
            "notif_channels": self.notif_channels or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_user_id": self.created_by_user_id,
            "updated_by_user_id": self.updated_by_user_id,
        }

    def __repr__(self):
        return (
            f"<AlertZone id={self.id} name={self.name} "
            f"min_mag={self.min_magnitude} max_mag={self.max_magnitude} enabled={self.enabled}>"
        )
