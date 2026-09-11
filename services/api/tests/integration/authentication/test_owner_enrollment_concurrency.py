from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from myhub.infrastructure.db.base import Base
from myhub.infrastructure.db.models import FamilyModel, InstanceBootstrapModel, MembershipModel, UserModel
from myhub.modules.administration.config import Settings
from myhub.modules.identity.auth_service import AuthService, InitialEnrollmentClosed


TOKEN = "postgres-auth-bootstrap-token-that-is-long-enough-123"
OWNER_ID = "20000000-0000-0000-0000-000000000001"
FAMILY_ID = "20000000-0000-0000-0000-000000000002"
MEMBERSHIP_ID = "20000000-0000-0000-0000-000000000003"


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="PostgreSQL URL not configured")
def test_concurrent_initial_owner_enrollment_has_one_winner() -> None:
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # The test seeds rows directly through independent ORM models without
    # relationship() edges. Flush explicitly in FK dependency order so the
    # fixture itself cannot race SQLAlchemy's unit-of-work insert ordering.
    with Session(engine) as session, session.begin():
        session.add(FamilyModel(id=FAMILY_ID, name="Concurrent Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Initial Owner"))
        session.flush()

        session.add(
            MembershipModel(
                id=MEMBERSHIP_ID,
                tenant_id=FAMILY_ID,
                user_id=OWNER_ID,
                role="Owner",
                status="ACTIVE",
            )
        )
        session.flush()

        session.add(
            InstanceBootstrapModel(
                id=1,
                state="READY",
                instance_id="20000000-0000-0000-0000-000000000004",
                canonical_url="https://family.example.com",
                family_id=FAMILY_ID,
                owner_user_id=OWNER_ID,
                owner_membership_id=MEMBERSHIP_ID,
            )
        )
        session.flush()

    settings = Settings(database_url=url, bootstrap_token=TOKEN)

    def run(index: int) -> str:
        with Session(engine) as session:
            service = AuthService(session=session, settings=settings)
            try:
                service.initial_owner_password_enroll(
                    bootstrap_token=TOKEN,
                    login_name=f"owner-{index}",
                    password=f"correct horse battery staple {index}",
                )
                return "enrolled"
            except InitialEnrollmentClosed:
                return "closed"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [1, 2]))

    assert sorted(results) == ["closed", "enrolled"]

    Base.metadata.drop_all(engine)
    engine.dispose()
