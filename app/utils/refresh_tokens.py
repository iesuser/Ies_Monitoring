"""Refresh-token persistence helpers (docs/05).

Policies implemented here:
- store hashed refresh JWT + jti/family metadata
- rotate on every successful refresh
- revoke whole family on reuse of a revoked token (replay mitigation)
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from app.extensions import db
from app.models import RefreshToken

logger = logging.getLogger("app.refresh_tokens")


class RefreshTokenError(Exception):
    """Raised when refresh-token validation fails."""

    def __init__(self, code: str, message: str, status_code: int = 401):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _client_meta():
    user_agent = request.headers.get("User-Agent") or ""
    return {
        "device_info": user_agent[:255] or None,
        "ip_address": (request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:45]
        or None,
    }


def _refresh_expires_at() -> datetime:
    delta = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES")
    if delta is None:
        raise RuntimeError("JWT_REFRESH_TOKEN_EXPIRES is not configured")
    return datetime.now() + delta


def _create_refresh_record(user, *, family_id: str, raw_refresh_token: str) -> RefreshToken:
    meta = _client_meta()
    record = RefreshToken(
        user_id=user.id,
        jti=get_jti(raw_refresh_token),
        family_id=family_id,
        token_hash=hash_token(raw_refresh_token),
        device_info=meta["device_info"],
        ip_address=meta["ip_address"],
        expires_at=_refresh_expires_at(),
    )
    record.create(commit=False)
    return record


def issue_token_pair(user):
    """Create access + refresh JWTs and persist the refresh session."""
    family_id = str(uuid.uuid4())
    raw_refresh = create_refresh_token(identity=user.uuid)
    record = _create_refresh_record(user, family_id=family_id, raw_refresh_token=raw_refresh)
    db.session.commit()

    access_token = create_access_token(identity=user.uuid)
    logger.info(
        "Issued refresh token: user_uuid=%s jti=%s family_id=%s",
        user.uuid,
        record.jti,
        record.family_id,
    )
    return access_token, raw_refresh, record


def revoke_family(family_id: str, *, commit: bool = True) -> int:
    """Revoke every still-active token in a refresh family."""
    now = datetime.now()
    tokens = (
        RefreshToken.query.filter_by(family_id=family_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for token in tokens:
        token.revoked_at = now
    if commit:
        db.session.commit()
    return len(tokens)


def revoke_token(record: RefreshToken, *, commit: bool = True) -> None:
    record.revoke(commit=commit)


def revoke_all_user_tokens(user_id: int, *, commit: bool = True) -> int:
    now = datetime.now()
    tokens = (
        RefreshToken.query.filter_by(user_id=user_id)
        .filter(RefreshToken.revoked_at.is_(None))
        .all()
    )
    for token in tokens:
        token.revoked_at = now
    if commit:
        db.session.commit()
    return len(tokens)


def find_by_jti(jti: str) -> RefreshToken | None:
    if not jti:
        return None
    return RefreshToken.query.filter_by(jti=jti).first()


def rotate_refresh_token(user, *, jti: str, raw_refresh_token: str):
    """Validate current refresh token, revoke it, issue a replacement in the same family."""
    record = find_by_jti(jti)
    if record is None:
        raise RefreshTokenError("token_revoked", "Refresh token is unknown or revoked.")

    if record.user_id != user.id:
        raise RefreshTokenError("token_revoked", "Refresh token does not belong to this user.")

    # Replay / reuse of an already-rotated or revoked token → kill the whole family.
    if record.revoked_at is not None:
        revoked_count = revoke_family(record.family_id)
        logger.warning(
            "Refresh token reuse detected: user_uuid=%s jti=%s family_id=%s revoked=%s",
            user.uuid,
            jti,
            record.family_id,
            revoked_count,
        )
        raise RefreshTokenError(
            "token_reused",
            "Refresh token reuse detected. All sessions in this family were revoked.",
        )

    if record.expires_at <= datetime.now():
        record.revoke()
        raise RefreshTokenError("token_expired", "Refresh token has expired.")

    if record.token_hash != hash_token(raw_refresh_token):
        revoke_family(record.family_id)
        logger.warning("Refresh token hash mismatch: user_uuid=%s jti=%s", user.uuid, jti)
        raise RefreshTokenError("token_revoked", "Refresh token is invalid.")

    now = datetime.now()
    raw_new_refresh = create_refresh_token(identity=user.uuid)
    new_record = _create_refresh_record(
        user,
        family_id=record.family_id,
        raw_refresh_token=raw_new_refresh,
    )
    db.session.flush()

    record.revoked_at = now
    record.last_used_at = now
    record.replaced_by_token_id = new_record.id
    db.session.commit()

    access_token = create_access_token(identity=user.uuid)
    logger.info(
        "Rotated refresh token: user_uuid=%s old_jti=%s new_jti=%s family_id=%s",
        user.uuid,
        record.jti,
        new_record.jti,
        record.family_id,
    )
    return access_token, raw_new_refresh, new_record


def get_raw_refresh_token_from_request() -> str | None:
    cookie_name = current_app.config.get("JWT_REFRESH_COOKIE_NAME", "refresh_token_cookie")
    return request.cookies.get(cookie_name)
