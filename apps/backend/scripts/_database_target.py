from urllib.parse import urlsplit

from app.core.config import Settings


def validate_database_target(settings: Settings, confirmed_database: str) -> str:
    settings.validate_runtime()
    if settings.database_url is None:
        raise ValueError("DATABASE_URL is required")
    database_name = urlsplit(settings.database_url).path.removeprefix("/")
    if not database_name or database_name in {"postgres", "template0", "template1"}:
        raise ValueError("Refusing to operate on a default PostgreSQL database")
    if confirmed_database != database_name:
        raise ValueError("--confirm-database must exactly match the DATABASE_URL database name")
    if settings.environment == "test" and not database_name.endswith("_test"):
        raise ValueError("Test operations require a database name ending in _test")
    return database_name


__all__ = ["validate_database_target"]
