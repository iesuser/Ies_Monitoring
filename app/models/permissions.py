from app.extensions import db
from app.models.base import BaseModel


class Permission(db.Model, BaseModel):
    __tablename__ = "permissions"

    id = db.Column(db.BigInteger, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    deactivated_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)

    created_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    updated_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    user_permissions = db.relationship("UserPermission", back_populates="permission", lazy="select")

    def __repr__(self):
        return f"<Permission code={self.code} active={self.is_active}>"
