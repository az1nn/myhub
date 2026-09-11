from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import InvitationModel, InvitationOnboardingContextModel
from myhub.modules.invitations.service import InvitationService, InvitationUnavailable


class OnboardingContextError(RuntimeError):
    pass


class OnboardingCredentialKind(StrEnum):
    PASSKEY = "passkey_registration"
    PASSWORD = "password_enrollment"


@dataclass(frozen=True, slots=True)
class IssuedOnboardingContext:
    context_id: str
    raw_context: str
    invitation_id: str
    purpose: OnboardingCredentialKind
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ResolvedOnboardingContext:
    context_id: str
    invitation_id: str
    tenant_id: str
    intended_role: str
    purpose: OnboardingCredentialKind
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class InvitationOnboardingService:
    """Issues short-lived invitation-scoped authority for SPEC-002 credential enrollment."""

    SECRET_BYTES = 32
    DEFAULT_TTL_SECONDS = 10 * 60
    MIN_TTL_SECONDS = 60
    MAX_TTL_SECONDS = 30 * 60

    def __init__(self, session: Session, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        if not self.MIN_TTL_SECONDS <= ttl_seconds <= self.MAX_TTL_SECONDS:
            raise ValueError("onboarding context TTL is outside the supported range")
        self.session = session
        self.ttl_seconds = ttl_seconds

    def issue_for_credential_enrollment(
        self,
        raw_invitation_token: str,
        *,
        purpose: str | OnboardingCredentialKind,
        now: datetime | None = None,
    ) -> IssuedOnboardingContext:
        normalized_purpose = self._purpose(purpose)
        invitation = InvitationService(self.session).resolve_usable(raw_invitation_token, now=now)
        issued_at = now or _utcnow()
        expires_at = min(
            issued_at + timedelta(seconds=self.ttl_seconds),
            _as_aware(invitation.expires_at),
        )
        context_id = str(uuid4())
        secret = secrets.token_bytes(self.SECRET_BYTES)
        encoded_secret = self._encode_secret(secret)
        self.session.add(
            InvitationOnboardingContextModel(
                id=context_id,
                invitation_id=invitation.id,
                secret_hash=hashlib.sha256(secret).hexdigest(),
                purpose=normalized_purpose.value,
                expires_at=expires_at,
                created_at=issued_at,
            )
        )
        self.session.flush()
        return IssuedOnboardingContext(
            context_id=context_id,
            raw_context=f"{context_id}.{encoded_secret}",
            invitation_id=invitation.id,
            purpose=normalized_purpose,
            expires_at=expires_at,
        )

    def resolve_for_credential_enrollment(
        self,
        raw_context: str,
        *,
        purpose: str | OnboardingCredentialKind,
        lock: bool = False,
        now: datetime | None = None,
    ) -> ResolvedOnboardingContext:
        normalized_purpose = self._purpose(purpose)
        context_id, secret = self._parse(raw_context)
        statement = select(InvitationOnboardingContextModel).where(
            InvitationOnboardingContextModel.id == context_id
        )
        if lock:
            statement = statement.with_for_update()
        context = self.session.scalar(statement)
        if context is None or context.purpose != normalized_purpose.value:
            raise OnboardingContextError("invalid onboarding context")
        candidate_hash = hashlib.sha256(secret).hexdigest()
        if not hmac.compare_digest(context.secret_hash, candidate_hash):
            raise OnboardingContextError("invalid onboarding context")

        checked_at = _as_aware(now or _utcnow())
        if context.consumed_at is not None or _as_aware(context.expires_at) <= checked_at:
            raise OnboardingContextError("invalid onboarding context")

        invitation = self.session.get(InvitationModel, context.invitation_id)
        if invitation is None:
            raise OnboardingContextError("invalid onboarding context")
        try:
            InvitationService.assert_usable(invitation, now=checked_at)
        except InvitationUnavailable as exc:
            raise OnboardingContextError("invalid onboarding context") from exc

        return ResolvedOnboardingContext(
            context_id=context.id,
            invitation_id=invitation.id,
            tenant_id=invitation.tenant_id,
            intended_role=invitation.intended_role,
            purpose=normalized_purpose,
            expires_at=_as_aware(context.expires_at),
        )

    def consume(
        self,
        raw_context: str,
        *,
        purpose: str | OnboardingCredentialKind,
        now: datetime | None = None,
    ) -> ResolvedOnboardingContext:
        resolved = self.resolve_for_credential_enrollment(
            raw_context,
            purpose=purpose,
            lock=True,
            now=now,
        )
        context = self.session.get(InvitationOnboardingContextModel, resolved.context_id)
        assert context is not None
        context.consumed_at = now or _utcnow()
        self.session.flush()
        return resolved

    @staticmethod
    def _purpose(value: str | OnboardingCredentialKind) -> OnboardingCredentialKind:
        try:
            return OnboardingCredentialKind(value)
        except ValueError as exc:
            raise OnboardingContextError("invalid onboarding context purpose") from exc

    @classmethod
    def _parse(cls, raw_context: str) -> tuple[str, bytes]:
        if not isinstance(raw_context, str) or raw_context.count(".") != 1:
            raise OnboardingContextError("invalid onboarding context")
        context_id, encoded_secret = raw_context.split(".", 1)
        try:
            normalized_id = str(UUID(context_id))
            secret = cls._decode_secret(encoded_secret)
        except (ValueError, AttributeError, base64.binascii.Error) as exc:
            raise OnboardingContextError("invalid onboarding context") from exc
        if len(secret) != cls.SECRET_BYTES:
            raise OnboardingContextError("invalid onboarding context")
        return normalized_id, secret

    @staticmethod
    def _encode_secret(secret: bytes) -> str:
        return base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode_secret(value: str) -> bytes:
        if not value:
            raise ValueError("empty onboarding secret")
        padding = "=" * (-len(value) % 4)
        return base64.b64decode(value + padding, altchars=b"-_", validate=True)
