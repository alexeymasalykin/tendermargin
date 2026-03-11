"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_projects_user", "projects", ["user_id"])

    op.create_table(
        "smeta_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "smeta_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("code", sa.String(100), server_default=""),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("quantity", sa.Numeric(15, 4), server_default="0"),
        sa.Column("unit_price", sa.Numeric(15, 2), server_default="0"),
        sa.Column("total_price", sa.Numeric(15, 2), server_default="0"),
        sa.Column("item_type", sa.String(50), server_default="unknown"),
        sa.Column("section", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_smeta_items_project", "smeta_items", ["project_id"])

    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("quantity", sa.Numeric(15, 4), server_default="0"),
        sa.Column("smeta_total", sa.Numeric(15, 2), server_default="0"),
        sa.Column("codes", sa.JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_materials_project", "materials", ["project_id"])

    op.create_table(
        "contractor_price_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fsnb_code", sa.String(100), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("price", sa.Numeric(15, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "fsnb_code", name="uq_library_user_code"),
    )
    op.create_index("idx_contractor_library_user_code", "contractor_price_library", ["user_id", "fsnb_code"])

    op.create_table(
        "contractor_prices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("smeta_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smeta_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fsnb_code", sa.String(100), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("price", sa.Numeric(15, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_contractor_prices_project", "contractor_prices", ["project_id"])
    op.create_index("idx_contractor_prices_smeta_item", "contractor_prices", ["smeta_item_id"])

    op.create_table(
        "pricelist_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("structure_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "pricelist_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_name", sa.Text, nullable=True),
        sa.Column("supplier_price", sa.Numeric(15, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_confidence_range"),
    )
    op.create_index("idx_pricelist_matches_project", "pricelist_matches", ["project_id"])


def downgrade() -> None:
    op.drop_table("pricelist_matches")
    op.drop_table("pricelist_uploads")
    op.drop_table("contractor_prices")
    op.drop_table("contractor_price_library")
    op.drop_table("materials")
    op.drop_table("smeta_items")
    op.drop_table("smeta_uploads")
    op.drop_table("projects")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
