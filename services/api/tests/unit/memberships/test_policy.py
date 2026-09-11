from __future__ import annotations

from myhub.modules.memberships.policy import (
    MembershipCapability,
    capabilities_for,
    has_capability,
)


def test_owner_has_membership_administration_capabilities() -> None:
    capabilities = capabilities_for(role="Owner", status="ACTIVE")
    assert capabilities == {
        MembershipCapability.READ,
        MembershipCapability.INVITE,
        MembershipCapability.REMOVE,
    }


def test_adult_and_member_are_read_only_for_membership_v01() -> None:
    assert capabilities_for(role="Adult", status="ACTIVE") == {MembershipCapability.READ}
    assert capabilities_for(role="Member", status="ACTIVE") == {MembershipCapability.READ}


def test_non_active_membership_has_no_capabilities() -> None:
    assert capabilities_for(role="Owner", status="REMOVED") == frozenset()
    assert not has_capability(role="Owner", status="SUSPENDED", capability="members.invite")


def test_unknown_role_or_capability_fails_closed() -> None:
    assert capabilities_for(role="Administrator", status="ACTIVE") == frozenset()
    assert not has_capability(role="Owner", status="ACTIVE", capability="members.superuser")


def test_route_policy_can_check_capability_without_role_conditionals() -> None:
    assert has_capability(role="Owner", status="ACTIVE", capability="members.invite")
    assert not has_capability(role="Adult", status="ACTIVE", capability="members.invite")
