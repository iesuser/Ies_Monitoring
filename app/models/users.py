import uuid
from datetime import datetime

from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import BaseModel
from app.utils.validators import normalize_email


class User(db.Model, BaseModel):
    __tablename__ = "users"

    # SQLite only autoincrements INTEGER PKs; keep BIGINT on MySQL/Postgres.
    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Profile fields
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Optional metadata fields
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_sent_email = db.Column(db.DateTime, nullable=True)

    # Audit fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())
    created_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    updated_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)

    user_permissions = db.relationship(
        "UserPermission",
        foreign_keys="UserPermission.user_id",
        back_populates="user",
        lazy="select",
    )

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def check_permission(self, permission_code):
        from app.utils.auth_utils import has_user_permission

        return has_user_permission(self, permission_code)

    @validates("email")
    def validate_and_normalize_email(self, _, email):
        return normalize_email(email)

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User uuid={self.uuid} email={self.email}>"