from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, InstanceBootstrapModel, InvitationModel, MembershipModel, UserModel
from myhub.modules.invitations.service import (
    InvitationRoleNotAllowed,
    InvitationService,
    InvitationUnavailable,
)
from myhub.modules.memberships.repository import MembershipUnauthorized


TENANT_ID = "50000000-0000-0000-0000-000000000001"
OWNER_ID = "50000000-0000-0000-0000-000000000002"
ADULT_ID = "50000000-0000-0000-0000-000000000003"


def _seed(session: Session) -> None:
    with session.begin():
        session.add(FamilyModel(id=TENANT_ID, name="Wave Three Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Owner"))
        session.add(UserModel(id=ADULT_ID, display_name="Adult"))
        session.flush()
        session.add(MembershipModel(id="50000000-0000-0000-0000-000000000010", tenant_id=TENANT_ID, user_id=OWNER_ID, role="Owner", status="ACTIVE"))
        session.add(MembershipModel(id="50000000-0000-0000-0000-000000000011", tenant_id=TENANT_ID, user_id=ADULT_ID, role="Adult", status="ACTIVE"))
        bootstrap = session.get(InstanceBootstrapModel, 1)
        assert bootstrap is not None
        bootstrap.instance_id = "50000000-0000-0000-0000-000000000099"
        bootstrap.canonical_url = "https://family.example.test"


def test_creation_requires_capability_and_never_persists_raw_secret(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with session.begin():
            created = InvitationService(session).create(
                tenant_id=TENANT_ID,
                actor_user_id=OWNER_ID,
                intended_role="Adult",
            )
            persisted = session.get(InvitationModel, created.invitation_id)
            assert persisted is not None
            assert persisted.token_hash not in created.raw_token
            assert created.expires_at - persisted.created_at == timedelta(days=1)

        with pytest.raises(MembershipUnauthorized):
            with session.begin():
                InvitationService(session).create(
                    tenant_id=TENANT_ID,
                    actor_user_id=ADULT_ID,
                    intended_role="Member",
                )


def test_normal_invitation_cannot_assign_owner(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with pytest.raises(InvitationRoleNotAllowed):
            with session.begin():
                InvitationService(session).create(
                    tenant_id=TENANT_ID,
                    actor_user_id=OWNER_ID,
                    intended_role="Owner",
                )


def test_preview_is_minimal_and_rejects_expired_or_revoked_invites(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with session.begin():
            service = InvitationService(session)
            created = service.create(
                tenant_id=TENANT_ID,
                actor_user_id=OWNER_ID,
                intended_role="Member",
            )
            preview = service.preview(created.raw_token)
            assert set(preview.__dataclass_fields__) == {
                "family_name",
                "server_url",
                "instance_id",
                "intended_role",
                "expires_at",
            }
            assert preview.family_name == "Wave Three Family"
            assert preview.server_url == "https://family.example.test"
            assert preview.intended_role == "Member"

            with pytest.raises(InvitationUnavailable):
                service.preview(created.raw_token, now=created.expires_at + timedelta(seconds=1))

            service.revoke(
                tenant_id=TENANT_ID,
                actor_user_id=OWNER_ID,
                invitation_id=created.invitation_id,
            )
            with pytest.raises(InvitationUnavailable):
                service.preview(created.raw_token)
