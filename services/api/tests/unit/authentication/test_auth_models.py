from __future__ import annotations

from myhub.infrastructure.db.models import (
    AuthChallengeModel,
    AuthSessionModel,
    InitialOwnerEnrollmentModel,
    PasskeyCredentialModel,
    PasswordCredentialModel,
)


def test_authentication_tables_are_registered() -> None:
    assert PasskeyCredentialModel.__tablename__ == "passkey_credentials"
    assert AuthChallengeModel.__tablename__ == "auth_challenges"
    assert PasswordCredentialModel.__tablename__ == "password_credentials"
    assert AuthSessionModel.__tablename__ == "auth_sessions"
    assert InitialOwnerEnrollmentModel.__tablename__ == "initial_owner_enrollment"


def test_passkey_credential_stores_server_verification_state() -> None:
    columns = PasskeyCredentialModel.__table__.columns
    assert {"credential_id", "credential_public_key", "sign_count", "backup_eligible", "backup_state"}.issubset(columns.keys())


def test_challenge_persistence_supports_expiry_and_single_use() -> None:
    columns = AuthChallengeModel.__table__.columns
    assert {"purpose", "challenge_hash", "expires_at", "consumed_at"}.issubset(columns.keys())


def test_session_persistence_stores_only_secret_hash() -> None:
    columns = AuthSessionModel.__table__.columns
    assert "secret_hash" in columns
    assert "secret" not in columns
    assert "token" not in columns


def test_password_credential_has_unique_login_name() -> None:
    constraint_names = {constraint.name for constraint in PasswordCredentialModel.__table__.constraints}
    assert "uq_password_login_name" in constraint_names
