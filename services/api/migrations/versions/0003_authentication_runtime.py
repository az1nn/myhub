"""add authentication runtime state

Revision ID: 0003_authentication_runtime
Revises: 0002_authentication_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_authentication_runtime"
down_revision = "0002_authentication_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("passkey_credentials", sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.add_column("password_credentials", sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_table(
        "login_throttles",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_login_throttles_blocked_until", "login_throttles", ["blocked_until"])


def downgrade() -> None:
    op.drop_index("ix_login_throttles_blocked_until", table_name="login_throttles")
    op.drop_table("login_throttles")
    op.drop_column("password_credentials", "revoked_at")
    op.drop_column("passkey_credentials", "revoked_at")
