from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from myhub.domain.bootstrap import BootstrapState
from myhub.infrastructure.db.base import Base
from myhub.infrastructure.db.models import InstanceBootstrapModel, MembershipModel
from myhub.infrastructure.identity import Ed25519InstanceIdentityProvider
from myhub.modules.administration.bootstrap_service import BootstrapCommand, BootstrapService, InstanceAlreadyInitialized

TOKEN = "postgres-bootstrap-token-that-is-long-enough-123"


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="PostgreSQL URL not configured")
def test_concurrent_bootstrap_creates_one_owner() -> None:
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add(InstanceBootstrapModel(id=1, state=BootstrapState.UNINITIALIZED.value))

    def run(index: int) -> str:
        with Session(engine) as session:
            service = BootstrapService(session=session, identity_provider=Ed25519InstanceIdentityProvider(), expected_token=TOKEN)
            try:
                service.bootstrap(BootstrapCommand(
                    family_name="Concurrent Family",
                    canonical_url="https://family.example.com",
                    owner_display_name=f"Owner {index}",
                    supplied_token=TOKEN,
                    request_id=f"race-{index}",
                ))
                return "created"
            except InstanceAlreadyInitialized:
                return "already-ready"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [1, 2]))

    assert sorted(results) == ["already-ready", "created"]
    with Session(engine) as session:
        assert len(session.query(MembershipModel).filter_by(role="Owner").all()) == 1

    Base.metadata.drop_all(engine)
    engine.dispose()
