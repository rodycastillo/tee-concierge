"""drop faq_entries: FAQ answers are now text nodes in the menu file

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("faq_entries")


def downgrade() -> None:
    op.create_table(
        "faq_entries",
        sa.Column("topic", sa.String(40), primary_key=True),
        sa.Column("body", sa.Text(), nullable=False),
    )
