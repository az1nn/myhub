from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import AuthChallengeModel


class ChallengePurpose(StrEnum):
    REGISTRATION = "registration"
    AUTHENTICATION = "authentication"


class ChallengeError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class IssuedChallenge:
    id: str
    token: str
    raw: bytes
    purpose: ChallengePurpose
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _encode_token(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode_token(token: str) -> bytes:
    try:
        encoded = token.encode("ascii")
        padding = b"=" * (-len(encoded) % 4)
        raw = base64.urlsafe_b64decode(encoded + padding)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ChallengeError("invalid_challenge") from exc
    if len(raw) != 32:
        raise ChallengeError("invalid_challenge")
    return raw


def _challenge_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ChallengeService:
    """Issues and atomically consumes short-lived WebAuthn challenges.

    Only a SHA-256 verifier is persisted. The transport token lets the caller
    reconstruct the expected raw WebAuthn challenge after the verifier has
    been matched to an unconsumed row.
    """

    def __init__(self, session: Session, *, ttl_seconds: int = 300) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.session = session
        self.ttl_seconds = ttl_seconds

    def issue(
        self,
        *,
        purpose: ChallengePurpose,
        user_id: str | None,
        now: datetime | None = None,
    ) -> IssuedChallenge:
        issued_at = now or _utcnow()
        raw = secrets.token_bytes(32)
        token = _encode_token(raw)
        expires_at = issued_at + timedelta(seconds=self.ttl_seconds)
        challenge_id = str(uuid4())

        self.session.add(
            AuthChallengeModel(
                id=challenge_id,
                user_id=user_id,
                purpose=purpose.value,
                challenge_hash=_challenge_hash(raw),
                expires_at=expires_at,
                created_at=issued_at,
            )
        )
        self.session.flush()
        return IssuedChallenge(
            id=challenge_id,
            token=token,
            raw=raw,
            purpose=purpose,
            expires_at=expires_at,
        )

    def consume(
        self,
        *,
        token: str,
        purpose: ChallengePurpose,
        user_id: str | None,
        now: datetime | None = None,
    ) -> bytes:
        consumed_at = now or _utcnow()
        raw = _decode_token(token)
        statement = (
            select(AuthChallengeModel)
            .where(AuthChallengeModel.challenge_hash == _challenge_hash(raw))
            .with_for_update()
        )
        record = self.session.scalar(statement)

        # Deliberately collapse unknown/purpose/user mismatches into one error.
        if (
            record is None
            or record.purpose != purpose.value
            or record.user_id != user_id
        ):
            raise ChallengeError("invalid_challenge")
        if record.consumed_at is not None:
            raise ChallengeError("challenge_replayed")
        if _as_aware(record.expires_at) <= _as_aware(consumed_at):
            raise ChallengeError("challenge_expired")

        record.consumed_at = consumed_at
        self.session.flush()
        return raw
