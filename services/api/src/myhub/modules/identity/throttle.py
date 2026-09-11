from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import LoginThrottleModel


class AuthenticationThrottled(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ThrottlePolicy:
    max_failures: int = 5
    window_seconds: int = 5 * 60
    block_seconds: int = 15 * 60

    def __post_init__(self) -> None:
        if self.max_failures < 1 or self.window_seconds < 1 or self.block_seconds < 1:
            raise ValueError("throttle policy values must be positive")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _key_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class LoginThrottleService:
    """Small-instance abuse control coordinated through PostgreSQL, not Redis.

    Callers should use opaque scopes such as `ip:<address>` and
    `login:<normalized-login-name>`. Only SHA-256 digests are persisted.
    """

    def __init__(self, session: Session, policy: ThrottlePolicy | None = None) -> None:
        self.session = session
        self.policy = policy or ThrottlePolicy()

    def check(self, *keys: str, now: datetime | None = None) -> None:
        checked_at = now or _utcnow()
        for key in keys:
            record = self._lock(key)
            if record is not None and record.blocked_until is not None:
                if _as_aware(record.blocked_until) > _as_aware(checked_at):
                    raise AuthenticationThrottled("authentication temporarily throttled")

    def record_failure(self, *keys: str, now: datetime | None = None) -> None:
        failed_at = now or _utcnow()
        for key in keys:
            digest = _key_hash(key)
            record = self._lock(key)
            if record is None:
                record = LoginThrottleModel(
                    key_hash=digest,
                    failures=0,
                    window_started_at=failed_at,
                    updated_at=failed_at,
                )
                self.session.add(record)
                self.session.flush()

            window_expired = _as_aware(record.window_started_at) + timedelta(
                seconds=self.policy.window_seconds
            ) <= _as_aware(failed_at)
            if window_expired:
                record.failures = 0
                record.window_started_at = failed_at
                record.blocked_until = None

            record.failures += 1
            record.updated_at = failed_at
            if record.failures >= self.policy.max_failures:
                record.blocked_until = failed_at + timedelta(seconds=self.policy.block_seconds)
            self.session.flush()

    def record_success(self, *keys: str) -> None:
        for key in keys:
            record = self._lock(key)
            if record is not None:
                self.session.delete(record)
        self.session.flush()

    def _lock(self, key: str) -> LoginThrottleModel | None:
        return self.session.scalar(
            select(LoginThrottleModel)
            .where(LoginThrottleModel.key_hash == _key_hash(key))
            .with_for_update()
        )
