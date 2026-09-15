from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import (
    AuthSessionModel,
    FamilyModel,
    InvitationModel,
    InvitationOnboardingContextModel,
    MembershipModel,
    PasskeyCredentialModel,
    PasswordCredentialModel,
    UserModel,
)
from myhub.modules.identity.passwords import PasswordService
from myhub.modules.identity.sessions import SessionService
from myhub.modules.invitations.acceptance import (
    InvitationAcceptanceConflict,
    InvitationAcceptanceService,
    InvitationAcceptanceUnavailable,
    VerifiedPasskeyEnrollment,
)
from myhub.modules.invitations.onboarding import (
    InvitationOnboardingService,
    OnboardingCredentialKind,
)
from myhub.modules.invitations.service import InvitationService


TENANT_ID = "70000000-0000-0000-0000-000000000001"
OWNER_ID = "70000000-0000-0000-0000-000000000002"
OWNER_MEMBERSHIP_ID = "70000000-0000-0000-0000-000000000003"


def _seed_owner(session: Session) -> None:
    with session.begin():
        session.add(FamilyModel(id=TENANT_ID, name="Acceptance Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Owner"))
        session.flush()
        session.add(
            MembershipModel(
                id=OWNER_MEMBERSHIP_ID,
                tenant_id=TENANT_ID,
                user_id=OWNER_ID,
                role="Owner",
                status="ACTIVE",
            )
        )


def _issue_context(
    session: Session,
    *,
    purpose: OnboardingCredentialKind,
):
    with session.begin():
        invitation = InvitationService(session).create(
            tenant_id=TENANT_ID,
            actor_user_id=OWNER_ID,
            intended_role="Member",
        )
    with session.begin():
        context = InvitationOnboardingService(session).issue_for_credential_enrollment(
            invitation.raw_token,
            purpose=purpose,
        )
    return invitation, context


def test_password_acceptance_is_atomic_and_establishes_normal_session(engine) -> None:
    with Session(engine) as session:
        _seed_owner(session)
        invitation, context = _issue_context(
            session,
            purpose=OnboardingCredentialKind.PASSWORD,
        )

        accepted = InvitationAcceptanceService(session).accept_password(
            context.raw_context,
            display_name="  Invited Member  ",
            login_name="Invited.Member",
            password="correct horse battery staple",
        )

        with session.begin():
            user = session.get(UserModel, accepted.user_id)
            membership = session.get(MembershipModel, accepted.membership_id)
            credential = session.scalar(
                select(PasswordCredentialModel).where(
                    PasswordCredentialModel.user_id == accepted.user_id
                )
            )
            stored_invitation = session.get(InvitationModel, invitation.invitation_id)
            stored_context = session.get(
                InvitationOnboardingContextModel,
                context.context_id,
            )
            stored_session = session.get(AuthSessionModel, accepted.session_id)

            assert user is not None
            assert user.display_name == "Invited Member"
            assert membership is not None
            assert membership.tenant_id == TENANT_ID
            assert membership.user_id == accepted.user_id
            assert membership.role == "Member"
            assert membership.status == "ACTIVE"

            assert credential is not None
            assert credential.login_name == "invited.member"
            assert credential.password_hash != "correct horse battery staple"
            assert PasswordService().verify(
                credential.password_hash,
                "correct horse battery staple",
            )

            assert stored_invitation is not None
            assert stored_invitation.consumed_at is not None
            assert stored_invitation.consumed_by_user_id == accepted.user_id
            assert stored_context is not None
            assert stored_context.consumed_at is not None
            assert stored_session is not None

            authenticated = SessionService(session).authenticate(accepted.bearer_token)
            assert authenticated.user_id == accepted.user_id


def test_credential_conflict_rolls_back_and_same_context_can_retry(engine) -> None:
    with Session(engine) as session:
        _seed_owner(session)
        invitation, context = _issue_context(
            session,
            purpose=OnboardingCredentialKind.PASSWORD,
        )

        existing_user_id = "70000000-0000-0000-0000-000000000099"
        with session.begin():
            session.add(UserModel(id=existing_user_id, display_name="Existing"))
            session.flush()
            session.add(
                PasswordCredentialModel(
                    id="70000000-0000-0000-0000-000000000098",
                    user_id=existing_user_id,
                    login_name="already-taken",
                    password_hash=PasswordService().hash("existing password"),
                )
            )

        acceptance = InvitationAcceptanceService(session)
        with pytest.raises(InvitationAcceptanceConflict):
            acceptance.accept_password(
                context.raw_context,
                display_name="Retry Member",
                login_name="already-taken",
                password="new password",
            )

        with session.begin():
            stored_invitation = session.get(InvitationModel, invitation.invitation_id)
            stored_context = session.get(
                InvitationOnboardingContextModel,
                context.context_id,
            )
            assert stored_invitation is not None
            assert stored_invitation.consumed_at is None
            assert stored_invitation.consumed_by_user_id is None
            assert stored_context is not None
            assert stored_context.consumed_at is None
            assert session.scalar(select(func.count()).select_from(UserModel)) == 2
            assert (
                session.scalar(select(func.count()).select_from(MembershipModel))
                == 1
            )
            assert (
                session.scalar(select(func.count()).select_from(AuthSessionModel))
                == 0
            )

        accepted = acceptance.accept_password(
            context.raw_context,
            display_name="Retry Member",
            login_name="retry-member",
            password="new password",
        )
        assert accepted.tenant_id == TENANT_ID


def test_two_contexts_for_one_invitation_still_allow_only_one_acceptance(engine) -> None:
    with Session(engine) as session:
        _seed_owner(session)
        with session.begin():
            invitation = InvitationService(session).create(
                tenant_id=TENANT_ID,
                actor_user_id=OWNER_ID,
                intended_role="Adult",
            )
        with session.begin():
            onboarding = InvitationOnboardingService(session)
            first = onboarding.issue_for_credential_enrollment(
                invitation.raw_token,
                purpose=OnboardingCredentialKind.PASSWORD,
            )
            second = onboarding.issue_for_credential_enrollment(
                invitation.raw_token,
                purpose=OnboardingCredentialKind.PASSWORD,
            )

        acceptance = InvitationAcceptanceService(session)
        winner = acceptance.accept_password(
            first.raw_context,
            display_name="Winner",
            login_name="winner",
            password="winner password",
        )
        assert winner.role == "Adult"

        with pytest.raises(InvitationAcceptanceUnavailable):
            acceptance.accept_password(
                second.raw_context,
                display_name="Loser",
                login_name="loser",
                password="loser password",
            )

        with session.begin():
            assert session.scalar(select(func.count()).select_from(UserModel)) == 2
            assert (
                session.scalar(select(func.count()).select_from(MembershipModel))
                == 2
            )
            assert (
                session.scalar(select(func.count()).select_from(PasswordCredentialModel))
                == 1
            )
            assert (
                session.scalar(select(func.count()).select_from(AuthSessionModel))
                == 1
            )


def test_verified_passkey_acceptance_persists_verified_material_and_session(engine) -> None:
    with Session(engine) as session:
        _seed_owner(session)
        invitation, context = _issue_context(
            session,
            purpose=OnboardingCredentialKind.PASSKEY,
        )
        ceremony_user_id = str(uuid4())
        verified = VerifiedPasskeyEnrollment(
            user_id=ceremony_user_id,
            credential_id=b"credential-id",
            credential_public_key=b"credential-public-key",
            sign_count=7,
            transports=("internal", "hybrid"),
            backup_eligible=True,
            backup_state=True,
        )

        accepted = InvitationAcceptanceService(session).accept_verified_passkey(
            context.raw_context,
            display_name="Passkey Member",
            credential=verified,
        )

        assert accepted.user_id == ceremony_user_id
        with session.begin():
            credential = session.scalar(
                select(PasskeyCredentialModel).where(
                    PasskeyCredentialModel.user_id == ceremony_user_id
                )
            )
            stored_invitation = session.get(InvitationModel, invitation.invitation_id)
            assert credential is not None
            assert credential.credential_id == b"credential-id"
            assert credential.credential_public_key == b"credential-public-key"
            assert credential.sign_count == 7
            assert credential.backup_eligible is True
            assert credential.backup_state is True
            assert stored_invitation is not None
            assert stored_invitation.consumed_by_user_id == ceremony_user_id

            authenticated = SessionService(session).authenticate(accepted.bearer_token)
            assert authenticated.user_id == ceremony_user_id
