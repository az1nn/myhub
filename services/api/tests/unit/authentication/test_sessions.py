from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import AuthSessionModel, UserModel
from myhub.modules.identity.sessions import SessionCredentialError, SessionService


NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
USER_ID = "00000000-0000-0000-0000-000000000001"


def seed_user(session: Session) -> None:
    session.add(UserModel(id=USER_ID, display_name="Alan", created_at=NOW))
    session.flush()


def test_session_stores_hash_not_bearer(engine) -> None:
    with Session(engine) as session, session.begin():
        seed_user(session)
        service = SessionService(session, ttl_seconds=3600)
        issued = service.issue(user_id=USER_ID, now=NOW)

        record = session.scalar(select(AuthSessionModel).where(AuthSessionModel.id == issued.id))
        assert record is not None
        assert record.secret_hash != issued.bearer_token
        assert len(record.secret_hash) == 64
        assert service.authenticate(issued.bearer_token, now=NOW + timedelta(seconds=1)).user_id == USER_ID


def test_revoked_session_is_rejected(engine) -> None:
    with Session(engine) as session, session.begin():
        seed_user(session)
        service = SessionService(session, ttl_seconds=3600)
        issued = service.issue(user_id=USER_ID, now=NOW)
        service.revoke(issued.bearer_token, now=NOW + timedelta(seconds=1))

        with pytest.raises(SessionCredentialError) as revoked:
            service.authenticate(issued.bearer_token, now=NOW + timedelta(seconds=2))
        assert revoked.value.code == "session_revoked"


def test_expired_session_is_rejected(engine) -> None:
    with Session(engine) as session, session.begin():
        seed_user(session)
        service = SessionService(session, ttl_seconds=300)
        issued = service.issue(user_id=USER_ID, now=NOW)

        with pytest.raises(SessionCredentialError) as expired:
            service.authenticate(issued.bearer_token, now=NOW + timedelta(seconds=301))
        assert expired.value.code == "session_expired"


def test_revoke_all_for_user(engine) -> None:
    with Session(engine) as session, session.begin():
        seed_user(session)
        service = SessionService(session, ttl_seconds=3600)
        first = service.issue(user_id=USER_ID, now=NOW)
        second = service.issue(user_id=USER_ID, now=NOW)

        assert service.revoke_all_for_user(USER_ID, now=NOW + timedelta(seconds=1)) == 2
        for token in (first.bearer_token, second.bearer_token):
            with pytest.raises(SessionCredentialError) as revoked:
                service.authenticate(token, now=NOW + timedelta(seconds=2))
            assert revoked.value.code == "session_revoked"
