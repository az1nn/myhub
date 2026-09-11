"""create instance bootstrap foundation

Revision ID: 0001_instance_bootstrap
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_instance_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "families",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),
    )
    op.create_table(
        "instance_bootstrap",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("instance_id", sa.String(36), unique=True),
        sa.Column("canonical_url", sa.String(512)),
        sa.Column("family_id", sa.String(36), unique=True),
        sa.Column("owner_user_id", sa.String(36), unique=True),
        sa.Column("owner_membership_id", sa.String(36), unique=True),
        sa.Column("server_public_key", sa.Text()),
        sa.Column("server_private_key_pem", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(sa.text("INSERT INTO instance_bootstrap (id, state, created_at, updated_at) VALUES (1, 'UNINITIALIZED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))


def downgrade() -> None:
    op.drop_table("instance_bootstrap")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("families")
