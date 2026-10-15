"""create cloud_resources table

Revision ID: 0001_cloud_resources
Revises: 
Create Date: 2026-10-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_cloud_resources"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cloud_resources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("service_type", sa.String(length=64), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False, server_default="ap-south-1"),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("monthly_cost", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="Optimal"),
        sa.Column("owner_team", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cloud_resources_id"), "cloud_resources", ["id"], unique=False)
    op.create_index(op.f("ix_cloud_resources_resource_name"), "cloud_resources", ["resource_name"], unique=False)
    op.create_index(op.f("ix_cloud_resources_provider"), "cloud_resources", ["provider"], unique=False)
    op.create_index(op.f("ix_cloud_resources_status"), "cloud_resources", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cloud_resources_status"), table_name="cloud_resources")
    op.drop_index(op.f("ix_cloud_resources_provider"), table_name="cloud_resources")
    op.drop_index(op.f("ix_cloud_resources_resource_name"), table_name="cloud_resources")
    op.drop_index(op.f("ix_cloud_resources_id"), table_name="cloud_resources")
    op.drop_table("cloud_resources")