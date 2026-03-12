"""Add supplier_price_library table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supplier_price_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("normalized_name", sa.Text, nullable=False),
        sa.Column("supplier_name", sa.Text, nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("source", sa.String(255), server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "normalized_name", "unit", name="uq_supplier_lib_user_name_unit"),
    )
    op.create_index("idx_supplier_lib_user", "supplier_price_library", ["user_id"])


def downgrade() -> None:
    op.drop_table("supplier_price_library")
