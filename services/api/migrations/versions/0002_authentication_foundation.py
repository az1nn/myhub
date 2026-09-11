"""create authentication foundation

Revision ID: 0002_authentication_foundation
Revises: 0001_instance_bootstrap
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_authentication_foundation"
down_revision = "0001_instance_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "passkey_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credential_id", sa.LargeBinary(), nullable=False),
        sa.Column("credential_public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("transports_json", sa.Text()),
        sa.Column("backup_eligible", sa.Boolean(), nullable=False),
        sa.Column("backup_state", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("credential_id", name="uq_passkey_credential_id"),
        sa.UniqueConstraint("user_id", "credential_id", name="uq_passkey_user_credential"),
    )

    op.create_table(
        "auth_challenges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("challenge_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("challenge_hash", name="uq_auth_challenge_hash"),
    )
    op.create_index("ix_auth_challenges_expiry", "auth_challenges", ["expires_at", "consumed_at"])

    op.create_table(
        "password_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("login_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_password_credential_user"),
        sa.UniqueConstraint("login_name", name="uq_password_login_name"),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("secret_hash", name="uq_auth_session_secret_hash"),
    )
    op.create_index("ix_auth_sessions_user_active", "auth_sessions", ["user_id", "expires_at", "revoked_at"])

    op.create_table(
        "initial_owner_enrollment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_initial_owner_enrollment_user"),
    )


def downgrade() -> None:
    op.drop_table("initial_owner_enrollment")
    op.drop_index("ix_auth_sessions_user_active", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("password_credentials")
    op.drop_index("ix_auth_challenges_expiry", table_name="auth_challenges")
    op.drop_table("auth_challenges")
    op.drop_table("passkey_credentials")
