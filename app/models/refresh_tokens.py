import uuid
from datetime import datetime

from app.extensions import db
from app.models.base import BaseModel


class RefreshToken(db.Model, BaseModel):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    family_id = db.Column(db.String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    token_hash = db.Column(db.String(255), nullable=False)

    replaced_by_token_id = db.Column(
        db.Integer,
        db.ForeignKey("refresh_tokens.id"),
        nullable=True,
    )

    device_info = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="refresh_tokens")
    replaced_by = db.relationship(
        "RefreshToken",
        remote_side=[id],
        foreign_keys=[replaced_by_token_id],
        uselist=False,
    )

    @property
    def is_active(self):
        if self.revoked_at is not None:
            return False
        return self.expires_at > datetime.now()

    def revoke(self, commit=True):
        if self.revoked_at is None:
            self.revoked_at = datetime.now()
            if commit:
                self.save()

    def __repr__(self):
        return (
            f"<RefreshToken id={self.id} user_id={self.user_id} "
            f"jti={self.jti} active={self.is_active}>"
        )
