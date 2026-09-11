from __future__ import annotations

from enum import StrEnum


class MembershipRole(StrEnum):
    OWNER = "Owner"
    ADULT = "Adult"
    MEMBER = "Member"


class MembershipCapability(StrEnum):
    READ = "members.read"
    INVITE = "members.invite"
    REMOVE = "members.remove"


ACTIVE_MEMBERSHIP_STATUS = "ACTIVE"

_ROLE_CAPABILITIES: dict[MembershipRole, frozenset[MembershipCapability]] = {
    MembershipRole.OWNER: frozenset(
        {
            MembershipCapability.READ,
            MembershipCapability.INVITE,
            MembershipCapability.REMOVE,
        }
    ),
    MembershipRole.ADULT: frozenset({MembershipCapability.READ}),
    MembershipRole.MEMBER: frozenset({MembershipCapability.READ}),
}


def capabilities_for(*, role: str, status: str) -> frozenset[MembershipCapability]:
    """Return backend-authoritative membership capabilities.

    A membership must be ACTIVE to authorize anything. Unknown roles fail closed.
    The initial V0.1 mapping is intentionally conservative: only Owner has
    membership-administration capabilities; Adult and Member may read membership
    information. Future expansion requires a specification/policy change rather
    than route-local role checks.
    """

    if status != ACTIVE_MEMBERSHIP_STATUS:
        return frozenset()

    try:
        normalized_role = MembershipRole(role)
    except ValueError:
        return frozenset()
    return _ROLE_CAPABILITIES[normalized_role]


def has_capability(*, role: str, status: str, capability: str | MembershipCapability) -> bool:
    try:
        required = MembershipCapability(capability)
    except ValueError:
        return False
    return required in capabilities_for(role=role, status=status)
