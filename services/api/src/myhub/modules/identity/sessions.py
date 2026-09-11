from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import AuthSessionModel


class SessionCredentialError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class IssuedSession:
    id: str
    bearer_token: str
    user_id: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    id: str
    user_id: str
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_bearer(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SessionService:
    """Issues high-entropy opaque bearer sessions and persists only verifiers."""

    def __init__(self, session: Session, *, ttl_seconds: int = 30 * 24 * 60 * 60) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.session = session
        self.ttl_seconds = ttl_seconds

    def issue(self, *, user_id: str, now: datetime | None = None) -> IssuedSession:
        issued_at = now or _utcnow()
        expires_at = issued_at + timedelta(seconds=self.ttl_seconds)
        bearer = secrets.token_urlsafe(32)
        session_id = str(uuid4())

        self.session.add(
            AuthSessionModel(
                id=session_id,
                user_id=user_id,
                secret_hash=_hash_bearer(bearer),
                expires_at=expires_at,
                created_at=issued_at,
            )
        )
        self.session.flush()
        return IssuedSession(
            id=session_id,
            bearer_token=bearer,
            user_id=user_id,
            expires_at=expires_at,
        )

    def authenticate(self, bearer_token: str, *, now: datetime | None = None) -> AuthenticatedSession:
        if not bearer_token:
            raise SessionCredentialError("invalid_session")
        checked_at = now or _utcnow()
        record = self.session.scalar(
            select(AuthSessionModel).where(AuthSessionModel.secret_hash == _hash_bearer(bearer_token))
        )
        if record is None:
            raise SessionCredentialError("invalid_session")
        if record.revoked_at is not None:
            raise SessionCredentialError("session_revoked")
        if _as_aware(record.expires_at) <= _as_aware(checked_at):
            raise SessionCredentialError("session_expired")

        return AuthenticatedSession(
            id=record.id,
            user_id=record.user_id,
            expires_at=_as_aware(record.expires_at),
        )

    def revoke(self, bearer_token: str, *, now: datetime | None = None) -> None:
        if not bearer_token:
            return
        record = self.session.scalar(
            select(AuthSessionModel)
            .where(AuthSessionModel.secret_hash == _hash_bearer(bearer_token))
            .with_for_update()
        )
        if record is None or record.revoked_at is not None:
            return
        record.revoked_at = now or _utcnow()
        self.session.flush()

    def revoke_all_for_user(self, user_id: str, *, now: datetime | None = None) -> int:
        revoked_at = now or _utcnow()
        records = self.session.scalars(
            select(AuthSessionModel)
            .where(AuthSessionModel.user_id == user_id, AuthSessionModel.revoked_at.is_(None))
            .with_for_update()
        ).all()
        for record in records:
            record.revoked_at = revoked_at
        self.session.flush()
        return len(records)
