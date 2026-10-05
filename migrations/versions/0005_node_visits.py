"""menu usage counters

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_visits",
        sa.Column("node", sa.String(64), primary_key=True),
        sa.Column(
            "visits",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_table("node_visits")
