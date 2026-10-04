"""create messages

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("wamid", sa.String(128), unique=True),
        sa.Column("direction", sa.String(3), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("reply_id", sa.String(200)),
        sa.Column("profile_name", sa.String(128)),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_messages_phone_id", "messages", ["phone", "id"])


def downgrade() -> None:
    op.drop_index("ix_messages_phone_id", table_name="messages")
    op.drop_table("messages")
