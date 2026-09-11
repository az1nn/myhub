from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, MembershipModel, UserModel
from myhub.modules.memberships.repository import (
    DuplicateMembership,
    InvalidMembershipRole,
    MembershipRepository,
    MembershipUnauthorized,
)


TENANT_A = "40000000-0000-0000-0000-000000000001"
TENANT_B = "40000000-0000-0000-0000-000000000002"
USER_ID = "40000000-0000-0000-0000-000000000003"
MEMBERSHIP_ID = "40000000-0000-0000-0000-000000000004"


def _seed(session: Session) -> None:
    with session.begin():
        session.add(FamilyModel(id=TENANT_A, name="Family A"))
        session.add(FamilyModel(id=TENANT_B, name="Family B"))
        session.add(UserModel(id=USER_ID, display_name="Member"))
        session.flush()


def test_membership_lookup_is_always_tenant_scoped(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with session.begin():
            membership = MembershipRepository(session).create(
                tenant_id=TENANT_A,
                user_id=USER_ID,
                role="Member",
            )
            membership_id = membership.id

        repository = MembershipRepository(session)
        assert repository.get(tenant_id=TENANT_A, membership_id=membership_id) is not None
        assert repository.get(tenant_id=TENANT_B, membership_id=membership_id) is None
        assert repository.find_for_user(tenant_id=TENANT_B, user_id=USER_ID) is None


def test_duplicate_tenant_user_membership_is_rejected(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        repository = MembershipRepository(session)
        with session.begin():
            repository.create(tenant_id=TENANT_A, user_id=USER_ID, role="Adult")

        with pytest.raises(DuplicateMembership):
            with session.begin():
                repository.create(tenant_id=TENANT_A, user_id=USER_ID, role="Member")


def test_same_user_may_have_distinct_tenant_memberships_at_domain_boundary(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        repository = MembershipRepository(session)
        with session.begin():
            first = repository.create(tenant_id=TENANT_A, user_id=USER_ID, role="Member")
            second = repository.create(tenant_id=TENANT_B, user_id=USER_ID, role="Member")
        assert first.tenant_id != second.tenant_id


def test_unknown_role_is_rejected(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        with pytest.raises(InvalidMembershipRole):
            with session.begin():
                MembershipRepository(session).create(
                    tenant_id=TENANT_A,
                    user_id=USER_ID,
                    role="Administrator",
                )


def test_capability_check_uses_active_tenant_membership(engine) -> None:
    with Session(engine) as session:
        _seed(session)
        repository = MembershipRepository(session)
        with session.begin():
            session.add(
                MembershipModel(
                    id=MEMBERSHIP_ID,
                    tenant_id=TENANT_A,
                    user_id=USER_ID,
                    role="Owner",
                    status="ACTIVE",
                )
            )

        assert repository.require_capability(
            tenant_id=TENANT_A,
            user_id=USER_ID,
            capability="members.invite",
        ).id == MEMBERSHIP_ID

        with pytest.raises(MembershipUnauthorized):
            repository.require_capability(
                tenant_id=TENANT_B,
                user_id=USER_ID,
                capability="members.invite",
            )

        # SELECTs above open an implicit SQLAlchemy 2 transaction. Close that
        # read boundary before starting the explicit membership-state mutation.
        session.rollback()
        with session.begin():
            owner = session.get(MembershipModel, MEMBERSHIP_ID)
            assert owner is not None
            owner.status = "REMOVED"

        with pytest.raises(MembershipUnauthorized):
            repository.require_capability(
                tenant_id=TENANT_A,
                user_id=USER_ID,
                capability="members.invite",
            )
