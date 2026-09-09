import argparse
import asyncio
import getpass
import os

from app.core.config import get_settings
from app.core.identifiers import new_uuid7
from app.core.password_policy import validate_new_password_length
from app.core.resources import create_resources
from app.core.security import PasswordManager
from app.db.models import Admin
from app.db.repositories import AdminRepository, SessionRepository
from app.db.transaction import transaction_scope
from app.domains.auth.schemas import normalize_username
from scripts._database_target import validate_database_target


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or explicitly reset the initial administrator")
    parser.add_argument("--username", required=True)
    parser.add_argument("--confirm-database", required=True)
    parser.add_argument("--reset-existing", action="store_true")
    parser.add_argument("--confirm-reset", action="store_true")
    return parser.parse_args()


def _password() -> str:
    value = os.environ.get("INITIAL_ADMIN_PASSWORD")
    if value is None:
        first = getpass.getpass("Initial administrator password: ")
        second = getpass.getpass("Confirm password: ")
        if first != second:
            raise ValueError("两次输入的密码不一致")
        value = first
    return validate_new_password_length(value)


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    validate_database_target(settings, args.confirm_database)
    username = normalize_username(args.username)
    password_hash = await PasswordManager(settings.password_hash_concurrency).hash(_password())
    resources = create_resources(settings)
    try:
        async with resources.session_factory() as session, transaction_scope(session):
            admins = AdminRepository(session)
            existing = await admins.get_by_username(username, for_update=True)
            if existing is None:
                admins.add(
                    Admin(
                        id=new_uuid7(),
                        username=username,
                        display_name=None,
                        password_hash=password_hash,
                        is_active=True,
                        is_superuser=True,
                        credential_version=1,
                    )
                )
                print("Initial administrator created")
                return
            if not args.reset_existing or not args.confirm_reset:
                raise ValueError("Administrator already exists; reset requires --reset-existing and --confirm-reset")
            existing.password_hash = password_hash
            existing.is_active = True
            existing.is_superuser = True
            existing.credential_version += 1
            await SessionRepository(session).revoke_admin_for_admin(existing.id, reason="initial_admin_reset")
            print("Existing administrator reset and sessions revoked")
    finally:
        await resources.close()


def main() -> None:
    asyncio.run(_run(_arguments()))


if __name__ == "__main__":
    main()
