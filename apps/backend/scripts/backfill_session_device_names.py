import argparse
import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.core.client_identity import session_device_name
from app.core.config import get_settings
from app.core.resources import create_resources
from app.db.models import AdminSession, UserSession
from app.db.transaction import transaction_scope
from scripts._database_target import validate_database_target


@dataclass(frozen=True, slots=True)
class BackfillSummary:
    candidates: int
    parseable: int
    unresolved: int


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or apply session device-name backfill")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-database", required=True)
    return parser.parse_args()


def _backfill_sessions(sessions: list[UserSession] | list[AdminSession], *, apply: bool) -> BackfillSummary:
    parseable = 0
    unresolved = 0
    for login_session in sessions:
        device_name = session_device_name(login_session.user_agent_summary)
        if device_name is None:
            unresolved += 1
            continue
        parseable += 1
        if apply:
            login_session.device_name = device_name
    return BackfillSummary(candidates=len(sessions), parseable=parseable, unresolved=unresolved)


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    validate_database_target(settings, args.confirm_database)
    resources = create_resources(settings)
    try:
        async with resources.session_factory() as session, transaction_scope(session):
            user_sessions = list(
                (
                    await session.scalars(
                        select(UserSession)
                        .where(UserSession.device_name.is_(None), UserSession.user_agent_summary.is_not(None))
                        .order_by(UserSession.id)
                    )
                ).all()
            )
            admin_sessions = list(
                (
                    await session.scalars(
                        select(AdminSession)
                        .where(AdminSession.device_name.is_(None), AdminSession.user_agent_summary.is_not(None))
                        .order_by(AdminSession.id)
                    )
                ).all()
            )
            user_summary = _backfill_sessions(user_sessions, apply=args.apply)
            admin_summary = _backfill_sessions(admin_sessions, apply=args.apply)

        print(
            f"user_candidates={user_summary.candidates} user_parseable={user_summary.parseable} "
            f"user_unresolved={user_summary.unresolved} admin_candidates={admin_summary.candidates} "
            f"admin_parseable={admin_summary.parseable} admin_unresolved={admin_summary.unresolved}"
        )
        if args.apply:
            print("Session device-name backfill applied")
        else:
            print("Dry run only; no rows updated")
        return 0
    finally:
        await resources.close()


def main() -> None:
    raise SystemExit(asyncio.run(_run(_arguments())))


if __name__ == "__main__":
    main()
