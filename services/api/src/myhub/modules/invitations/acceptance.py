from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import (
    InvitationModel,
    InvitationOnboardingContextModel,
    PasskeyCredentialModel,
    PasswordCredentialModel,
    UserModel,
)
from myhub.modules.identity.passwords import (
    Argon2idPolicy,
    LoginNameError,
    PasswordService,
    normalize_login_name,
)
from myhub.modules.identity.sessions import SessionService
from myhub.modules.invitations.onboarding import (
    InvitationOnboardingService,
    OnboardingContextError,
    OnboardingCredentialKind,
)
from myhub.modules.invitations.service import InvitationService, InvitationUnavailable
from myhub.modules.memberships.repository import MembershipRepository


class InvitationAcceptanceError(RuntimeError):
    pass


class InvitationAcceptanceUnavailable(InvitationAcceptanceError):
    """The scoped onboarding authority or invitation can no longer be accepted."""


class InvitationAcceptanceConflict(InvitationAcceptanceError):
    """A credential or persistence invariant conflicted with existing state."""


class InvitationCredentialInvalid(InvitationAcceptanceError):
    """Credential/profile material is not valid for invitation acceptance."""


@dataclass(frozen=True, slots=True)
class VerifiedPasskeyEnrollment:
    """Passkey material that SPEC-002 has already cryptographically verified.

    The invitation service intentionally does not duplicate WebAuthn verification.
    The caller must pass the same user handle used by the verified registration
    ceremony as ``user_id`` so later WebAuthn authentication can validate it.
    """

    user_id: str
    credential_id: bytes
    credential_public_key: bytes
    sign_count: int
    transports: tuple[str, ...] = ()
    backup_eligible: bool = False
    backup_state: bool = False


@dataclass(frozen=True, slots=True)
class AcceptedInvitation:
    invitation_id: str
    tenant_id: str
    user_id: str
    membership_id: str
    role: str
    session_id: str
    bearer_token: str
    session_expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class InvitationAcceptanceService:
    """Atomic invitation acceptance and single-use enforcement.

    Credential verification/preparation happens before the transaction where
    practical. The transaction then locks/revalidates the scoped onboarding
    context and invitation, creates identity + membership + credential + session,
    and consumes both one-use authorities. Any failure rolls the whole unit back.
    """

    def __init__(
        self,
        session: Session,
        *,
        password_policy: Argon2idPolicy | None = None,
        session_ttl_seconds: int = 30 * 24 * 60 * 60,
    ) -> None:
        self.session = session
        self.passwords = PasswordService(password_policy)
        self.session_ttl_seconds = session_ttl_seconds

    def accept_password(
        self,
        raw_context: str,
        *,
        display_name: str,
        login_name: str,
        password: str,
        now: datetime | None = None,
    ) -> AcceptedInvitation:
        normalized_display_name = self._display_name(display_name)
        try:
            canonical_login = normalize_login_name(login_name)
            encoded_hash = self.passwords.hash(password)
        except (LoginNameError, ValueError) as exc:
            raise InvitationCredentialInvalid("invalid password enrollment") from exc

        user_id = str(uuid4())

        def persist_credential() -> None:
            self.session.add(
                PasswordCredentialModel(
                    id=str(uuid4()),
                    user_id=user_id,
                    login_name=canonical_login,
                    password_hash=encoded_hash,
                )
            )

        return self._accept(
            raw_context,
            purpose=OnboardingCredentialKind.PASSWORD,
            display_name=normalized_display_name,
            user_id=user_id,
            persist_credential=persist_credential,
            now=now,
        )

    def accept_verified_passkey(
        self,
        raw_context: str,
        *,
        display_name: str,
        credential: VerifiedPasskeyEnrollment,
        now: datetime | None = None,
    ) -> AcceptedInvitation:
        normalized_display_name = self._display_name(display_name)
        user_id = self._passkey_user_id(credential)

        def persist_credential() -> None:
            self.session.add(
                PasskeyCredentialModel(
                    id=str(uuid4()),
                    user_id=user_id,
                    credential_id=credential.credential_id,
                    credential_public_key=credential.credential_public_key,
                    sign_count=credential.sign_count,
                    transports_json=(
                        json.dumps(list(credential.transports))
                        if credential.transports
                        else None
                    ),
                    backup_eligible=credential.backup_eligible,
                    backup_state=credential.backup_state,
                )
            )

        return self._accept(
            raw_context,
            purpose=OnboardingCredentialKind.PASSKEY,
            display_name=normalized_display_name,
            user_id=user_id,
            persist_credential=persist_credential,
            now=now,
        )

    def _accept(
        self,
        raw_context: str,
        *,
        purpose: OnboardingCredentialKind,
        display_name: str,
        user_id: str,
        persist_credential,
        now: datetime | None,
    ) -> AcceptedInvitation:
        accepted_at = _as_aware(now or _utcnow())

        try:
            with self.session.begin():
                onboarding = InvitationOnboardingService(self.session)
                resolved = onboarding.resolve_for_credential_enrollment(
                    raw_context,
                    purpose=purpose,
                    lock=True,
                    now=accepted_at,
                )

                invitation = self.session.scalar(
                    select(InvitationModel)
                    .where(
                        InvitationModel.id == resolved.invitation_id,
                        InvitationModel.tenant_id == resolved.tenant_id,
                    )
                    .with_for_update()
                )
                if invitation is None:
                    raise InvitationAcceptanceUnavailable("invitation unavailable")
                InvitationService.assert_usable(invitation, now=accepted_at)

                user = UserModel(
                    id=user_id,
                    display_name=display_name,
                    created_at=accepted_at,
                )
                self.session.add(user)
                self.session.flush()

                membership = MembershipRepository(self.session).create(
                    tenant_id=resolved.tenant_id,
                    user_id=user_id,
                    role=resolved.intended_role,
                    status="ACTIVE",
                )
                persist_credential()
                self.session.flush()

                context_result = self.session.execute(
                    update(InvitationOnboardingContextModel)
                    .where(
                        InvitationOnboardingContextModel.id == resolved.context_id,
                        InvitationOnboardingContextModel.invitation_id
                        == resolved.invitation_id,
                        InvitationOnboardingContextModel.purpose == purpose.value,
                        InvitationOnboardingContextModel.consumed_at.is_(None),
                        InvitationOnboardingContextModel.expires_at > accepted_at,
                    )
                    .values(consumed_at=accepted_at)
                )
                if context_result.rowcount != 1:
                    raise InvitationAcceptanceUnavailable("onboarding context unavailable")

                invitation_result = self.session.execute(
                    update(InvitationModel)
                    .where(
                        InvitationModel.id == resolved.invitation_id,
                        InvitationModel.tenant_id == resolved.tenant_id,
                        InvitationModel.consumed_at.is_(None),
                        InvitationModel.revoked_at.is_(None),
                        InvitationModel.expires_at > accepted_at,
                    )
                    .values(
                        consumed_at=accepted_at,
                        consumed_by_user_id=user_id,
                    )
                )
                if invitation_result.rowcount != 1:
                    raise InvitationAcceptanceUnavailable("invitation unavailable")

                issued_session = SessionService(
                    self.session,
                    ttl_seconds=self.session_ttl_seconds,
                ).issue(user_id=user_id, now=accepted_at)

                result = AcceptedInvitation(
                    invitation_id=resolved.invitation_id,
                    tenant_id=resolved.tenant_id,
                    user_id=user_id,
                    membership_id=membership.id,
                    role=resolved.intended_role,
                    session_id=issued_session.id,
                    bearer_token=issued_session.bearer_token,
                    session_expires_at=issued_session.expires_at,
                )
            return result
        except InvitationAcceptanceUnavailable:
            raise
        except (OnboardingContextError, InvitationUnavailable) as exc:
            raise InvitationAcceptanceUnavailable("invitation unavailable") from exc
        except IntegrityError as exc:
            raise InvitationAcceptanceConflict("acceptance conflicts with existing state") from exc

    @staticmethod
    def _display_name(value: str) -> str:
        if not isinstance(value, str):
            raise InvitationCredentialInvalid("invalid display name")
        normalized = value.strip()
        if not 1 <= len(normalized) <= 80:
            raise InvitationCredentialInvalid("invalid display name")
        return normalized

    @staticmethod
    def _passkey_user_id(credential: VerifiedPasskeyEnrollment) -> str:
        try:
            normalized_user_id = str(UUID(credential.user_id))
        except (ValueError, AttributeError) as exc:
            raise InvitationCredentialInvalid("invalid verified passkey user id") from exc
        if not credential.credential_id or not credential.credential_public_key:
            raise InvitationCredentialInvalid("invalid verified passkey credential")
        if credential.sign_count < 0:
            raise InvitationCredentialInvalid("invalid verified passkey sign count")
        return normalized_user_id
