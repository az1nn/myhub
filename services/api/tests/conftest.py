from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from myhub.app.main import create_app
from myhub.domain.bootstrap import BootstrapState
from myhub.infrastructure.db.base import Base
from myhub.infrastructure.db.models import InstanceBootstrapModel
from myhub.modules.administration.config import Settings

TEST_TOKEN = "test-bootstrap-token-that-is-long-enough-12345"


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add(InstanceBootstrapModel(id=1, state=BootstrapState.UNINITIALIZED.value))
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine) -> Iterator[TestClient]:
    settings = Settings(database_url="sqlite+pysqlite:///:memory:", bootstrap_token=TEST_TOKEN)
    app = create_app(settings=settings, engine=engine)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
