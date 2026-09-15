from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import MembershipModel
from myhub.modules.identity.sessions import SessionService
from myhub.modules.memberships.policy import ACTIVE_MEMBERSHIP_STATUS, MembershipCapability, MembershipRole
from myhub.modules.memberships.repository import MembershipRepository


class MembershipLifecycleError(RuntimeError):
    pass


class MembershipNotRemovable(MembershipLifecycleError):
    pass


class LastOwnerRemovalForbidden(MembershipLifecycleError):
    pass


@dataclass(frozen=True, slots=True)
class RemovedMembership:
    membership_id: str
    tenant_id: str
    user_id: str
    role: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MembershipLifecycleService:
    """Tenant-scoped membership state transitions with backend authorization."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def remove(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        membership_id: str,
        now: datetime | None = None,
    ) -> RemovedMembership:
        repository = MembershipRepository(self.session)
        repository.require_capability(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            capability=MembershipCapability.REMOVE,
            lock=True,
        )
        target = repository.get(
            tenant_id=tenant_id,
            membership_id=membership_id,
            lock=True,
        )
        if target is None or target.status != ACTIVE_MEMBERSHIP_STATUS:
            raise MembershipNotRemovable("membership is not removable")

        if target.role == MembershipRole.OWNER.value:
            active_owner_count = self.session.scalar(
                select(func.count())
                .select_from(MembershipModel)
                .where(
                    MembershipModel.tenant_id == tenant_id,
                    MembershipModel.role == MembershipRole.OWNER.value,
                    MembershipModel.status == ACTIVE_MEMBERSHIP_STATUS,
                )
            )
            if not active_owner_count or active_owner_count <= 1:
                raise LastOwnerRemovalForbidden("last Owner cannot be removed")

        target.status = "REMOVED"
        self.session.flush()

        # Defense in depth only. Authorization correctness still depends on the
        # membership state transition above rather than on session revocation.
        SessionService(self.session).revoke_all_for_user(target.user_id, now=now or _utcnow())
        return RemovedMembership(
            membership_id=target.id,
            tenant_id=target.tenant_id,
            user_id=target.user_id,
            role=target.role,
        )
