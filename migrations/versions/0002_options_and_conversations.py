"""store reply options and conversation state

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("options", sa.JSON()))
    op.create_table(
        "conversations",
        sa.Column("phone", sa.String(32), primary_key=True),
        sa.Column("node", sa.String(64), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversations")
    op.drop_column("messages", "options")
