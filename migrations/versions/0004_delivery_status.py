"""outbound delivery status

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("status", sa.String(16)))
    op.add_column("messages", sa.Column("status_at", sa.DateTime(timezone=True)))
    op.add_column("messages", sa.Column("status_error", sa.String(200)))


def downgrade() -> None:
    op.drop_column("messages", "status_error")
    op.drop_column("messages", "status_at")
    op.drop_column("messages", "status")
