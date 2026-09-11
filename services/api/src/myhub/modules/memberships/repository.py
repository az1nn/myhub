from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import MembershipModel
from myhub.modules.memberships.policy import MembershipCapability, MembershipRole, has_capability


class MembershipRepositoryError(RuntimeError):
    pass


class DuplicateMembership(MembershipRepositoryError):
    pass


class InvalidMembershipRole(MembershipRepositoryError):
    pass


class MembershipUnauthorized(MembershipRepositoryError):
    pass


class MembershipRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, *, tenant_id: str, membership_id: str, lock: bool = False) -> MembershipModel | None:
        statement = select(MembershipModel).where(
            MembershipModel.tenant_id == tenant_id,
            MembershipModel.id == membership_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def find_for_user(
        self,
        *,
        tenant_id: str,
        user_id: str,
        lock: bool = False,
    ) -> MembershipModel | None:
        statement = select(MembershipModel).where(
            MembershipModel.tenant_id == tenant_id,
            MembershipModel.user_id == user_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def create(
        self,
        *,
        tenant_id: str,
        user_id: str,
        role: str,
        status: str = "ACTIVE",
    ) -> MembershipModel:
        try:
            normalized_role = MembershipRole(role)
        except ValueError as exc:
            raise InvalidMembershipRole("unsupported membership role") from exc

        if self.find_for_user(tenant_id=tenant_id, user_id=user_id, lock=True) is not None:
            raise DuplicateMembership("membership already exists for tenant and user")

        membership = MembershipModel(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            role=normalized_role.value,
            status=status,
        )
        self.session.add(membership)
        self.session.flush()
        return membership

    def require_capability(
        self,
        *,
        tenant_id: str,
        user_id: str,
        capability: str | MembershipCapability,
        lock: bool = False,
    ) -> MembershipModel:
        membership = self.find_for_user(
            tenant_id=tenant_id,
            user_id=user_id,
            lock=lock,
        )
        if membership is None or not has_capability(
            role=membership.role,
            status=membership.status,
            capability=capability,
        ):
            raise MembershipUnauthorized("membership is not authorized for capability")
        return membership
