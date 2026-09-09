"""Create strongly typed runtime system settings.

Revision ID: 20260828_01
Revises: 20260827_03
Create Date: 2026-08-28
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260828_01"
down_revision: str | None = "20260827_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SITE_SETTING_ID = "0198f8a0-0000-7000-8000-000000000001"
_REGISTRATION_SETTING_ID = "0198f8a0-0000-7000-8000-000000000002"


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("setting_group", sa.String(length=50), nullable=False, comment="源码声明的固定设置分组"),
        sa.Column(
            "setting_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="分组完整 JSON 对象"
        ),
        sa.Column("revision", sa.Integer(), nullable=False, comment="乐观并发修订号"),
        sa.Column("updated_by", sa.Uuid(), nullable=True, comment="最后修改设置的管理员唯一标识"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_system_settings_revision_positive"),
        sa.CheckConstraint("jsonb_typeof(setting_value) = 'object'", name="ck_system_settings_value_object"),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["admins.id"], name="fk_system_settings_updated_by_admins", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("setting_group", name="uq_system_settings_setting_group"),
        comment="按固定分组保存的运行时系统设置",
    )
    settings = sa.table(
        "system_settings",
        sa.column("id", sa.Uuid()),
        sa.column("setting_group", sa.String()),
        sa.column("setting_value", postgresql.JSONB()),
        sa.column("revision", sa.Integer()),
        sa.column("updated_by", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        settings,
        [
            {
                "id": uuid.UUID(_SITE_SETTING_ID),
                "setting_group": "site",
                "setting_value": {
                    "name": "Pinjie",
                    "logo": None,
                    "title": "Pinjie",
                    "keywords": [],
                    "description": "通用全栈应用基础",
                },
                "revision": 1,
                "updated_by": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
            {
                "id": uuid.UUID(_REGISTRATION_SETTING_ID),
                "setting_group": "registration",
                "setting_value": {"enabled": False},
                "revision": 1,
                "updated_by": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("system_settings")
