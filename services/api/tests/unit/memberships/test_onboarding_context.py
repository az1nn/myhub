from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, InvitationModel, InvitationOnboardingContextModel, MembershipModel, UserModel
from myhub.modules.identity.sessions import SessionCredentialError, SessionService
from myhub.modules.invitations.onboarding import (
    InvitationOnboardingService,
    OnboardingContextError,
    OnboardingCredentialKind,
)
from myhub.modules.invitations.service import InvitationService


TENANT_ID = "60000000-0000-0000-0000-000000000001"
OWNER_ID = "60000000-0000-0000-0000-000000000002"


def _seed_invitation(session: Session):
    with session.begin():
        session.add(FamilyModel(id=TENANT_ID, name="Onboarding Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Owner"))
        session.flush()
        session.add(MembershipModel(id="60000000-0000-0000-0000-000000000010", tenant_id=TENANT_ID, user_id=OWNER_ID, role="Owner", status="ACTIVE"))
    with session.begin():
        return InvitationService(session).create(
            tenant_id=TENANT_ID,
            actor_user_id=OWNER_ID,
            intended_role="Member",
        )


def test_onboarding_context_is_short_lived_hashed_and_not_a_session(engine) -> None:
    with Session(engine) as session:
        invitation = _seed_invitation(session)
        with session.begin():
            issued = InvitationOnboardingService(session).issue_for_credential_enrollment(
                invitation.raw_token,
                purpose=OnboardingCredentialKind.PASSKEY,
            )
            stored = session.get(InvitationOnboardingContextModel, issued.context_id)
            assert stored is not None
            assert stored.secret_hash not in issued.raw_context
            assert stored.invitation_id == invitation.invitation_id
            assert stored.purpose == "passkey_registration"

            resolved = InvitationOnboardingService(session).resolve_for_credential_enrollment(
                issued.raw_context,
                purpose=OnboardingCredentialKind.PASSKEY,
            )
            assert resolved.tenant_id == TENANT_ID
            assert resolved.intended_role == "Member"

            with pytest.raises(SessionCredentialError):
                SessionService(session).authenticate(issued.raw_context)


def test_context_is_bound_to_credential_kind_and_live_invitation(engine) -> None:
    with Session(engine) as session:
        invitation = _seed_invitation(session)
        with session.begin():
            onboarding = InvitationOnboardingService(session)
            issued = onboarding.issue_for_credential_enrollment(
                invitation.raw_token,
                purpose=OnboardingCredentialKind.PASSWORD,
            )
            with pytest.raises(OnboardingContextError):
                onboarding.resolve_for_credential_enrollment(
                    issued.raw_context,
                    purpose=OnboardingCredentialKind.PASSKEY,
                )

            stored_invitation = session.get(InvitationModel, invitation.invitation_id)
            assert stored_invitation is not None
            stored_invitation.revoked_at = stored_invitation.created_at
            session.flush()
            with pytest.raises(OnboardingContextError):
                onboarding.resolve_for_credential_enrollment(
                    issued.raw_context,
                    purpose=OnboardingCredentialKind.PASSWORD,
                )


def test_consumed_context_cannot_be_reused(engine) -> None:
    with Session(engine) as session:
        invitation = _seed_invitation(session)
        with session.begin():
            onboarding = InvitationOnboardingService(session)
            issued = onboarding.issue_for_credential_enrollment(
                invitation.raw_token,
                purpose=OnboardingCredentialKind.PASSKEY,
            )
            onboarding.consume(issued.raw_context, purpose=OnboardingCredentialKind.PASSKEY)
            with pytest.raises(OnboardingContextError):
                onboarding.resolve_for_credential_enrollment(
                    issued.raw_context,
                    purpose=OnboardingCredentialKind.PASSKEY,
                )
