import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_settings"
    __table_args__ = (
        CheckConstraint("jsonb_typeof(setting_value) = 'object'", name="ck_system_settings_value_object"),
        CheckConstraint("revision > 0", name="ck_system_settings_revision_positive"),
        {"comment": "按固定分组保存的运行时系统设置"},
    )

    setting_group: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="源码声明的固定设置分组"
    )
    setting_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, comment="分组完整 JSON 对象")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="乐观并发修订号")
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        "updated_by",
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
        comment="最后修改设置的管理员唯一标识",
    )


__all__ = ["SystemSetting"]
