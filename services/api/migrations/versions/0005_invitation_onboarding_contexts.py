"""add invitation onboarding contexts

Revision ID: 0005_invite_onboarding_ctx
Revises: 0004_membership_invitations
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_invite_onboarding_ctx"
down_revision = "0004_membership_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invitation_onboarding_contexts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "invitation_id",
            sa.String(36),
            sa.ForeignKey("invitations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("secret_hash", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("secret_hash", name="uq_invitation_onboarding_secret_hash"),
    )
    op.create_index(
        "ix_invitation_onboarding_invitation_id",
        "invitation_onboarding_contexts",
        ["invitation_id"],
    )
    op.create_index(
        "ix_invitation_onboarding_expires_at",
        "invitation_onboarding_contexts",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_invitation_onboarding_expires_at", table_name="invitation_onboarding_contexts")
    op.drop_index("ix_invitation_onboarding_invitation_id", table_name="invitation_onboarding_contexts")
    op.drop_table("invitation_onboarding_contexts")
