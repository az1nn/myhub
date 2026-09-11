from __future__ import annotations

from sqlalchemy import CheckConstraint, UniqueConstraint

from myhub.infrastructure.db.models import InvitationModel


def test_invitation_persists_verifier_not_raw_token() -> None:
    columns = set(InvitationModel.__table__.columns.keys())
    assert "token_hash" in columns
    assert "token" not in columns
    assert "secret" not in columns


def test_invitation_has_single_use_lifecycle_fields() -> None:
    columns = set(InvitationModel.__table__.columns.keys())
    assert {
        "expires_at",
        "consumed_at",
        "consumed_by_user_id",
        "revoked_at",
    }.issubset(columns)


def test_invitation_token_verifier_is_unique() -> None:
    constraints = InvitationModel.__table__.constraints
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_invitation_token_hash"
        for constraint in constraints
    )


def test_normal_invitation_role_excludes_owner_at_database_boundary() -> None:
    constraints = InvitationModel.__table__.constraints
    role_constraint = next(
        constraint
        for constraint in constraints
        if isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_invitation_intended_role"
    )
    sql = str(role_constraint.sqltext)
    assert "Adult" in sql
    assert "Member" in sql
    assert "Owner" not in sql
