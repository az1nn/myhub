from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, MembershipModel, UserModel
from myhub.modules.identity.sessions import SessionCredentialError, SessionService
from myhub.modules.memberships.lifecycle import LastOwnerRemovalForbidden, MembershipLifecycleService
from myhub.modules.memberships.repository import MembershipRepository, MembershipUnauthorized


TENANT_ID = "70000000-0000-0000-0000-000000000001"
OWNER_ID = "70000000-0000-0000-0000-000000000002"
MEMBER_ID = "70000000-0000-0000-0000-000000000003"
OWNER_MEMBERSHIP_ID = "70000000-0000-0000-0000-000000000010"
MEMBER_MEMBERSHIP_ID = "70000000-0000-0000-0000-000000000011"


def _seed(session: Session) -> None:
    with session.begin():
        session.add(FamilyModel(id=TENANT_ID, name="Lifecycle Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Owner"))
        session.add(UserModel(id=MEMBER_ID, display_name="Member"))
        session.flush()
        session.add(MembershipModel(id=OWNER_MEMBERSHIP_ID, tenant_id=TENANT_ID, user_id=OWNER_ID, role="Owner", status="ACTIVE"))
        session.add(MembershipModel(id=MEMBER_MEMBERSHIP_ID, tenant_id=TENANT_ID, user_id=MEMBER_ID, role="Member", status="ACTIVE"))


def test_removal_changes_authorization_immediately_and_revokes_sessions(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with session.begin():
            member_session = SessionService(session).issue(user_id=MEMBER_ID)
            removed = MembershipLifecycleService(session).remove(
                tenant_id=TENANT_ID,
                actor_user_id=OWNER_ID,
                membership_id=MEMBER_MEMBERSHIP_ID,
            )
            assert removed.user_id == MEMBER_ID

        target = session.get(MembershipModel, MEMBER_MEMBERSHIP_ID)
        assert target is not None
        assert target.status == "REMOVED"
        with pytest.raises(MembershipUnauthorized):
            MembershipRepository(session).require_capability(
                tenant_id=TENANT_ID,
                user_id=MEMBER_ID,
                capability="members.read",
            )
        with pytest.raises(SessionCredentialError, match="session_revoked"):
            SessionService(session).authenticate(member_session.bearer_token)


def test_last_owner_cannot_be_removed(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with pytest.raises(LastOwnerRemovalForbidden):
            with session.begin():
                MembershipLifecycleService(session).remove(
                    tenant_id=TENANT_ID,
                    actor_user_id=OWNER_ID,
                    membership_id=OWNER_MEMBERSHIP_ID,
                )
        owner = session.get(MembershipModel, OWNER_MEMBERSHIP_ID)
        assert owner is not None
        assert owner.status == "ACTIVE"
