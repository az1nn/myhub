from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, InstanceBootstrapModel, InvitationModel
from myhub.modules.invitations.tokens import InvitationTokenError, InvitationTokenService
from myhub.modules.memberships.policy import MembershipCapability, MembershipRole
from myhub.modules.memberships.repository import MembershipRepository


class InvitationServiceError(RuntimeError):
    pass


class InvitationUnavailable(InvitationServiceError):
    pass


class InvitationRoleNotAllowed(InvitationServiceError):
    pass


class InvitationTtlInvalid(InvitationServiceError):
    pass


@dataclass(frozen=True, slots=True)
class IssuedInvitation:
    invitation_id: str
    raw_token: str
    tenant_id: str
    intended_role: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class InvitationPreview:
    family_name: str
    server_url: str
    instance_id: str
    intended_role: str
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class InvitationService:
    """Capability-protected invitation lifecycle without turning invites into sessions."""

    DEFAULT_TTL_SECONDS = 24 * 60 * 60
    MIN_TTL_SECONDS = 5 * 60
    MAX_TTL_SECONDS = 7 * 24 * 60 * 60

    def __init__(self, session: Session, *, default_ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.session = session
        self.default_ttl_seconds = self._validate_ttl(default_ttl_seconds)

    def create(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        intended_role: str,
        ttl_seconds: int | None = None,
        now: datetime | None = None,
    ) -> IssuedInvitation:
        MembershipRepository(self.session).require_capability(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            capability=MembershipCapability.INVITE,
        )

        try:
            role = MembershipRole(intended_role)
        except ValueError as exc:
            raise InvitationRoleNotAllowed("unsupported invitation role") from exc
        if role is MembershipRole.OWNER:
            raise InvitationRoleNotAllowed("Owner cannot be assigned by normal invitation")

        lifetime = self._validate_ttl(ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds)
        issued_at = now or _utcnow()
        issued = InvitationTokenService.issue()
        expires_at = issued_at + timedelta(seconds=lifetime)

        self.session.add(
            InvitationModel(
                id=issued.invitation_id,
                tenant_id=tenant_id,
                created_by_user_id=actor_user_id,
                intended_role=role.value,
                token_hash=issued.token_hash,
                expires_at=expires_at,
                created_at=issued_at,
            )
        )
        self.session.flush()
        return IssuedInvitation(
            invitation_id=issued.invitation_id,
            raw_token=issued.raw_token,
            tenant_id=tenant_id,
            intended_role=role.value,
            expires_at=expires_at,
        )

    def revoke(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        invitation_id: str,
        now: datetime | None = None,
    ) -> InvitationModel:
        MembershipRepository(self.session).require_capability(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            capability=MembershipCapability.INVITE,
        )
        invitation = self.session.scalar(
            select(InvitationModel)
            .where(
                InvitationModel.id == invitation_id,
                InvitationModel.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        if invitation is None or invitation.consumed_at is not None:
            raise InvitationUnavailable("invitation unavailable")
        if invitation.revoked_at is None:
            invitation.revoked_at = now or _utcnow()
            self.session.flush()
        return invitation

    def preview(self, raw_token: str, *, now: datetime | None = None) -> InvitationPreview:
        invitation = self.resolve_usable(raw_token, now=now)
        family = self.session.get(FamilyModel, invitation.tenant_id)
        instance = self.session.get(InstanceBootstrapModel, 1)
        if (
            family is None
            or instance is None
            or not instance.canonical_url
            or not instance.instance_id
        ):
            raise InvitationUnavailable("invitation instance unavailable")
        return InvitationPreview(
            family_name=family.name,
            server_url=instance.canonical_url,
            instance_id=instance.instance_id,
            intended_role=invitation.intended_role,
            expires_at=_as_aware(invitation.expires_at),
        )

    def resolve_usable(
        self,
        raw_token: str,
        *,
        lock: bool = False,
        now: datetime | None = None,
    ) -> InvitationModel:
        try:
            invitation = InvitationTokenService(self.session).resolve(raw_token, lock=lock)
        except InvitationTokenError as exc:
            raise InvitationUnavailable("invitation unavailable") from exc
        self.assert_usable(invitation, now=now)
        return invitation

    @staticmethod
    def assert_usable(invitation: InvitationModel, *, now: datetime | None = None) -> None:
        checked_at = _as_aware(now or _utcnow())
        if invitation.revoked_at is not None or invitation.consumed_at is not None:
            raise InvitationUnavailable("invitation unavailable")
        if _as_aware(invitation.expires_at) <= checked_at:
            raise InvitationUnavailable("invitation unavailable")

    @classmethod
    def _validate_ttl(cls, ttl_seconds: int) -> int:
        if not cls.MIN_TTL_SECONDS <= ttl_seconds <= cls.MAX_TTL_SECONDS:
            raise InvitationTtlInvalid(
                f"invitation TTL must be between {cls.MIN_TTL_SECONDS} and {cls.MAX_TTL_SECONDS} seconds"
            )
        return ttl_seconds
