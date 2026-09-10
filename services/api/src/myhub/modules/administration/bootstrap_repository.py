from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.domain.bootstrap import BootstrapState
from myhub.infrastructure.db.models import FamilyModel, InstanceBootstrapModel, MembershipModel, UserModel

BOOTSTRAP_ROW_ID = 1


class BootstrapRepository:
    def __init__(self, session: Session):
        self.session = session

    def lock(self) -> InstanceBootstrapModel:
        stmt = select(InstanceBootstrapModel).where(InstanceBootstrapModel.id == BOOTSTRAP_ROW_ID).with_for_update()
        record = self.session.scalar(stmt)
        if record is None:
            record = InstanceBootstrapModel(id=BOOTSTRAP_ROW_ID, state=BootstrapState.UNINITIALIZED.value)
            self.session.add(record)
            self.session.flush()
            record = self.session.scalar(stmt)
            assert record is not None
        return record

    def create_family(self, name: str) -> FamilyModel:
        family = FamilyModel(id=str(uuid.uuid4()), name=name)
        self.session.add(family)
        self.session.flush()
        return family

    def create_owner(self, tenant_id: str, display_name: str) -> tuple[UserModel, MembershipModel]:
        user = UserModel(id=str(uuid.uuid4()), display_name=display_name)
        membership = MembershipModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user.id,
            role="Owner",
            status="active",
        )
        self.session.add_all([user, membership])
        self.session.flush()
        return user, membership
