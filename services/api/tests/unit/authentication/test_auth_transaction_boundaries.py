from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import (
    AuthChallengeModel,
    FamilyModel,
    InstanceBootstrapModel,
    LoginThrottleModel,
    MembershipModel,
    PasswordCredentialModel,
    UserModel,
)
from myhub.modules.administration.config import Settings
from myhub.modules.identity.auth_service import AuthService, InvalidCredentials, TooManyAuthenticationAttempts
from tests.conftest import TEST_TOKEN


OWNER_ID = "00000000-0000-0000-0000-000000000001"
FAMILY_ID = "00000000-0000-0000-0000-000000000002"
MEMBERSHIP_ID = "00000000-0000-0000-0000-000000000003"


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        bootstrap_token=TEST_TOKEN,
        auth_login_max_failures=3,
        auth_login_window_seconds=300,
        auth_login_block_seconds=900,
    )


def _prepare_ready_instance(session: Session) -> None:
    with session.begin():
        session.add(FamilyModel(id=FAMILY_ID, name="Family Test"))
        session.add(UserModel(id=OWNER_ID, display_name="Initial Owner"))
        session.add(
            MembershipModel(
                id=MEMBERSHIP_ID,
                tenant_id=FAMILY_ID,
                user_id=OWNER_ID,
                role="Owner",
                status="ACTIVE",
            )
        )
        record = session.get(InstanceBootstrapModel, 1)
        assert record is not None
        record.state = "READY"
        record.instance_id = "00000000-0000-0000-0000-000000000004"
        record.canonical_url = "https://family.example.com"
        record.family_id = FAMILY_ID
        record.owner_user_id = OWNER_ID
        record.owner_membership_id = MEMBERSHIP_ID


def test_failed_passkey_attempt_keeps_challenge_consumed(engine) -> None:
    with Session(engine) as session:
        _prepare_ready_instance(session)
        service = AuthService(session=session, settings=_settings())
        options = service.passkey_authentication_options(client_key="127.0.0.1")

        with pytest.raises(InvalidCredentials):
            service.verify_passkey_authentication(
                challenge_token=options.challenge_token,
                credential={},
                client_key="127.0.0.1",
            )

    with Session(engine) as session:
        challenge = session.scalar(select(AuthChallengeModel))
        assert challenge is not None
        assert challenge.consumed_at is not None


def test_failed_password_attempts_commit_throttle_state(engine) -> None:
    settings = _settings()
    with Session(engine) as session:
        _prepare_ready_instance(session)
        service = AuthService(session=session, settings=settings)
        with session.begin():
            session.add(
                PasswordCredentialModel(
                    id="00000000-0000-0000-0000-000000000005",
                    user_id=OWNER_ID,
                    login_name="owner",
                    password_hash=service.passwords.hash("correct horse battery staple"),
                )
            )

        for _ in range(3):
            with pytest.raises(InvalidCredentials):
                service.password_login(
                    login_name="owner",
                    password="wrong password",
                    client_key="127.0.0.1",
                )

        with pytest.raises(TooManyAuthenticationAttempts):
            service.password_login(
                login_name="owner",
                password="correct horse battery staple",
                client_key="127.0.0.1",
            )

    with Session(engine) as session:
        records = session.scalars(select(LoginThrottleModel)).all()
        assert len(records) == 2
        assert {record.failures for record in records} == {3}
        assert all(record.blocked_until is not None for record in records)
