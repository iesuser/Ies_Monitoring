from app.extensions import db
from app.models.base import BaseModel


class UserPermission(db.Model, BaseModel):
    __tablename__ = "user_permissions"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, index=True)
    permission_id = db.Column(db.BigInteger, db.ForeignKey("permissions.id"), nullable=False, index=True)

    granted_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    granted_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    degranted_at = db.Column(db.DateTime, nullable=True)
    degranted_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="user_permissions")
    permission = db.relationship("Permission", foreign_keys=[permission_id], back_populates="user_permissions")

    __table_args__ = (
        db.Index("ix_user_permissions_user_permission_active", "user_id", "permission_id", "degranted_at"),
    )

    def __repr__(self):
        return (
            f"<UserPermission user_id={self.user_id} permission_id={self.permission_id} "
            f"active={self.degranted_at is None}>"
        )
