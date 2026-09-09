import argparse
import asyncio
from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.resources import create_resources
from app.db.repositories import SystemSettingRepository
from app.db.transaction import transaction_scope
from app.domains.settings.schemas import RegistrationSettingValue
from scripts._database_target import validate_database_target


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set public registration state in an isolated test database")
    parser.add_argument("--enabled", action=argparse.BooleanOptionalAction, required=True)
    parser.add_argument("--confirm-database", required=True)
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    if settings.environment != "test":
        raise ValueError("This helper only operates when ENVIRONMENT=test")
    validate_database_target(settings, args.confirm_database)
    resources = create_resources(settings)
    try:
        async with resources.session_factory() as session, transaction_scope(session):
            setting = await SystemSettingRepository(session).get("registration", for_update=True)
            if setting is None:
                raise RuntimeError("registration setting is missing; run Alembic first")
            value = RegistrationSettingValue(enabled=args.enabled)
            setting.setting_value = value.model_dump(mode="json")
            setting.revision += 1
            setting.updated_by_id = None
            setting.updated_at = datetime.now(UTC)
        print(f"test registration enabled={args.enabled}")
        return 0
    finally:
        await resources.close()


def main() -> None:
    raise SystemExit(asyncio.run(_run(_arguments())))


if __name__ == "__main__":
    main()
