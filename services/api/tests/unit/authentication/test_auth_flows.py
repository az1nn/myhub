from __future__ import annotations

import base64
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from webauthn.helpers.structs import CredentialDeviceType

from myhub.infrastructure.db.models import (
    AuthSessionModel,
    FamilyModel,
    InitialOwnerEnrollmentModel,
    InstanceBootstrapModel,
    MembershipModel,
    PasskeyCredentialModel,
    UserModel,
)
from myhub.modules.administration.config import Settings
from myhub.modules.identity.auth_service import AuthService, InitialEnrollmentClosed, InvalidCredentials
from myhub.modules.identity.challenges import ChallengePurpose
from tests.conftest import TEST_TOKEN


OWNER_ID = "10000000-0000-0000-0000-000000000001"
FAMILY_ID = "10000000-0000-0000-0000-000000000002"
MEMBERSHIP_ID = "10000000-0000-0000-0000-000000000003"


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        bootstrap_token=TEST_TOKEN,
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
        record.instance_id = "10000000-0000-0000-0000-000000000004"
        record.canonical_url = "https://family.example.com"
        record.family_id = FAMILY_ID
        record.owner_user_id = OWNER_ID
        record.owner_membership_id = MEMBERSHIP_ID


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class FakeProvider:
    def verify_registration(self, *, credential, expected_challenge):
        assert expected_challenge
        return SimpleNamespace(
            credential_id=b"owner-passkey",
            credential_public_key=b"owner-public-key",
            sign_count=0,
            credential_device_type=CredentialDeviceType.SINGLE_DEVICE,
            credential_backed_up=False,
        )

    def verify_authentication(
        self,
        *,
        credential,
        expected_challenge,
        credential_public_key,
        credential_current_sign_count,
    ):
        assert expected_challenge
        assert credential_public_key == b"owner-public-key"
        return SimpleNamespace(
            new_sign_count=credential_current_sign_count + 1,
            credential_device_type=CredentialDeviceType.SINGLE_DEVICE,
            credential_backed_up=False,
        )


def test_initial_owner_passkey_closes_bootstrap_enrollment_permanently(engine, monkeypatch) -> None:
    with Session(engine) as session:
        _prepare_ready_instance(session)
        service = AuthService(session=session, settings=_settings())
        monkeypatch.setattr(service, "_provider", lambda instance: FakeProvider())

        with session.begin():
            challenge = service.challenges.issue(
                purpose=ChallengePurpose.REGISTRATION,
                user_id=OWNER_ID,
            )

        result = service.verify_initial_owner_passkey(
            bootstrap_token=TEST_TOKEN,
            challenge_token=challenge.token,
            credential={"response": {"transports": ["internal"]}},
        )
        assert result.user_id == OWNER_ID
        assert result.bearer_token

        with pytest.raises(InitialEnrollmentClosed):
            service.initial_owner_password_enroll(
                bootstrap_token=TEST_TOKEN,
                login_name="owner",
                password="correct horse battery staple",
            )

    with Session(engine) as session:
        enrollment = session.get(InitialOwnerEnrollmentModel, 1)
        assert enrollment is not None
        assert enrollment.status == "COMPLETED"
        assert enrollment.completed_at is not None
        assert session.scalar(select(PasskeyCredentialModel)) is not None
        assert session.scalar(select(AuthSessionModel)) is not None


def test_verified_passkey_updates_counter_and_replay_fails(engine, monkeypatch) -> None:
    with Session(engine) as session:
        _prepare_ready_instance(session)
        with session.begin():
            session.add(
                PasskeyCredentialModel(
                    id="10000000-0000-0000-0000-000000000005",
                    user_id=OWNER_ID,
                    credential_id=b"owner-passkey",
                    credential_public_key=b"owner-public-key",
                    sign_count=7,
                    backup_eligible=False,
                    backup_state=False,
                )
            )

        service = AuthService(session=session, settings=_settings())
        monkeypatch.setattr(service, "_provider", lambda instance: FakeProvider())
        with session.begin():
            challenge = service.challenges.issue(
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
            )

        credential = {
            "id": _b64url(b"owner-passkey"),
            "response": {"userHandle": _b64url(OWNER_ID.encode("utf-8"))},
        }
        result = service.verify_passkey_authentication(
            challenge_token=challenge.token,
            credential=credential,
            client_key="127.0.0.1",
        )
        assert result.user_id == OWNER_ID

        with pytest.raises(InvalidCredentials):
            service.verify_passkey_authentication(
                challenge_token=challenge.token,
                credential=credential,
                client_key="127.0.0.1",
            )

    with Session(engine) as session:
        stored = session.scalar(select(PasskeyCredentialModel))
        assert stored is not None
        assert stored.sign_count == 8
        assert stored.last_used_at is not None


def test_revoked_passkey_is_rejected_before_verification(engine, monkeypatch) -> None:
    with Session(engine) as session:
        _prepare_ready_instance(session)
        with session.begin():
            session.add(
                PasskeyCredentialModel(
                    id="10000000-0000-0000-0000-000000000006",
                    user_id=OWNER_ID,
                    credential_id=b"revoked-passkey",
                    credential_public_key=b"owner-public-key",
                    sign_count=0,
                    backup_eligible=False,
                    backup_state=False,
                    revoked_at=datetime.now(timezone.utc),
                )
            )

        service = AuthService(session=session, settings=_settings())
        provider = FakeProvider()
        monkeypatch.setattr(service, "_provider", lambda instance: provider)
        with session.begin():
            challenge = service.challenges.issue(
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
            )

        with pytest.raises(InvalidCredentials):
            service.verify_passkey_authentication(
                challenge_token=challenge.token,
                credential={"id": _b64url(b"revoked-passkey"), "response": {}},
                client_key="127.0.0.1",
            )
