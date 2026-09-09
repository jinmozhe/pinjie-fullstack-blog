import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Admin, SystemSetting


class SystemSettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        setting_group: str,
        *,
        for_update: bool = False,
        for_share: bool = False,
    ) -> SystemSetting | None:
        statement = select(SystemSetting).where(SystemSetting.setting_group == setting_group)
        if for_update:
            statement = statement.with_for_update()
        elif for_share:
            statement = statement.with_for_update(read=True)
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def get_admin_summary(self, admin_id: uuid.UUID | None) -> tuple[uuid.UUID, str | None] | None:
        if admin_id is None:
            return None
        row = (
            await self._session.execute(select(Admin.id, Admin.display_name).where(Admin.id == admin_id))
        ).one_or_none()
        if row is None:
            return None
        return row.id, row.display_name


__all__ = ["SystemSettingRepository"]
